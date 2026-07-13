import logging
import json
from typing import TypedDict, List, Dict, Any, Optional, Callable
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.db_manager import SessionLocal

# Importando os nós dos agentes
from app.agents.asset_registry import run_asset_registry
from app.agents.real_estate import run_real_estate_agent
from app.agents.fixed_income import run_fixed_income_agent
from app.agents.project_viability import run_project_viability_agent
from app.agents.scenario_modeling import run_scenario_modeling_agent
from app.agents.comparative_decision import run_comparative_decision_agent
from app.agents.ai_advisor import run_ai_advisor_agent

# Definição do Estado do Grafo do NOVA
class NOVAState(TypedDict):
    query: str
    asset_ids: List[int]
    temporary_assets: List[Dict[str, Any]]
    assets_data: List[Dict[str, Any]]
    analyzed_assets: List[Dict[str, Any]]
    simulations: Dict[int, Dict[str, Any]]
    ranking: List[Dict[str, Any]]
    recommendation: str
    errors: List[str]

def safe_node(func: Callable[[NOVAState], dict]) -> Callable[[NOVAState], dict]:
    """
    Corporate Standard Docstring: safe_node
    Decorador para execução segura de nós do LangGraph.
    Captura exceções para impedir colapso do StateGraph, registrando o erro em state["errors"].
    """
    def wrapper(state: NOVAState) -> dict:
        try:
            return func(state)
        except Exception as e:
            error_msg = f"Error in node {func.__name__}: {str(e)}"
            logging.error(error_msg)
            errors = state.get("errors", []) + [error_msg]
            return {"errors": errors}
    return wrapper

def create_nova_graph() -> StateGraph:
    """Cria e compila o StateGraph para o pipeline do NOVA."""
    workflow = StateGraph(NOVAState)
    
    # Adicionando os nós correspondentes aos sub-agentes com safe_node
    workflow.add_node("asset_registry", safe_node(run_asset_registry))
    workflow.add_node("real_estate", safe_node(run_real_estate_agent))
    workflow.add_node("fixed_income", safe_node(run_fixed_income_agent))
    workflow.add_node("project_viability", safe_node(run_project_viability_agent))
    workflow.add_node("scenario_modeling", safe_node(run_scenario_modeling_agent))
    workflow.add_node("comparative_decision", safe_node(run_comparative_decision_agent))
    workflow.add_node("ai_advisor", safe_node(run_ai_advisor_agent))
    
    # Definindo o fluxo sequencial estrito do pipeline
    workflow.set_entry_point("asset_registry")
    workflow.add_edge("asset_registry", "real_estate")
    workflow.add_edge("real_estate", "fixed_income")
    workflow.add_edge("fixed_income", "project_viability")
    workflow.add_edge("project_viability", "scenario_modeling")
    workflow.add_edge("scenario_modeling", "comparative_decision")
    workflow.add_edge("comparative_decision", "ai_advisor")
    workflow.add_edge("ai_advisor", END)
    
    return workflow.compile()

def save_comparison_to_db(state: NOVAState) -> Optional[int]:
    """
    Grava de forma atômica e consistente os resultados da comparação no banco SQLite.
    Salva o histórico da pergunta, do ranking obtido e do parecer qualitativo.
    Também persiste os resultados estatísticos do Monte Carlo correspondentes na tabela simulation_results.
    """
    query_text = state.get("query", "Comparação Sem Nome")
    asset_ids = state.get("asset_ids", [])
    
    # Converte IDs comparados em string ex: "1,2,5"
    compared_ids_str = ",".join([str(int(i)) for i in asset_ids])
    
    ranking_json = json.dumps(state.get("ranking", []), ensure_ascii=False)
    advisor_narrative = state.get("recommendation", "")
    
    logging.info("[Orchestrator DB] Salvando histórico de comparação no SQLite.")
    
    comparison_id = None
    with SessionLocal() as db:
        try:
            # 1. Insere histórico na tabela comparison_history
            result = db.execute(
                text("""
                    INSERT INTO comparison_history (query_text, compared_asset_ids, ranking_json, advisor_narrative)
                    VALUES (:query_text, :compared_asset_ids, :ranking_json, :advisor_narrative)
                    RETURNING id
                """),
                {
                    "query_text": query_text,
                    "compared_asset_ids": compared_ids_str,
                    "ranking_json": ranking_json,
                    "advisor_narrative": advisor_narrative
                }
            )
            row = result.fetchone()
            if row:
                comparison_id = row[0]
                
            # 2. Persiste os resultados de simulação individual
            for asset_id, sim in state.get("simulations", {}).items():
                # ativos temporários têm IDs negativos, não relacionamos com tabela assets no foreign key se for menor que 0
                db_asset_id = asset_id if asset_id > 0 else None
                
                # Converte parâmetros específicos do Monte Carlo
                params = {
                    "asset_type": sim.get("asset_type"),
                    "mean_return": sim.get("mean_return"),
                    "std_dev": sim.get("std_dev")
                }
                metrics = {
                    "p10": sim.get("p10_return"),
                    "p50": sim.get("p50_return"),
                    "p90": sim.get("p90_return"),
                    "loss_probability": sim.get("loss_probability"),
                    "raw_distribution": sim.get("raw_distribution")
                }
                
                db.execute(
                    text("""
                        INSERT INTO simulation_results (asset_id, simulation_type, parameters_json, metrics_json)
                        VALUES (:asset_id, 'monte_carlo', :params_json, :metrics_json)
                    """),
                    {
                        "asset_id": db_asset_id,
                        "params_json": json.dumps(params),
                        "metrics_json": json.dumps(metrics)
                    }
                )
                
            db.commit()
            logging.info(f"[Orchestrator DB] Comparação persistida com sucesso. ID histórico: {comparison_id}")
        except Exception as e:
            db.rollback()
            logging.error(f"[Orchestrator DB] Falha ao persistir comparação no banco: {e}")
            raise e
        
    return comparison_id

def run_nova_comparison_pipeline(
    query: str,
    asset_ids: List[int],
    temporary_assets: Optional[List[Dict[str, Any]]] = None
) -> dict:
    """
    Função de interface para execução da comparação multi-agente do NOVA.
    Carrega o grafo de estados, executa o workflow e salva os resultados.
    """
    initial_state = NOVAState(
        query=query,
        asset_ids=asset_ids,
        temporary_assets=temporary_assets or [],
        assets_data=[],
        analyzed_assets=[],
        simulations={},
        ranking=[],
        recommendation="",
        errors=[]
    )
    
    # Compila e executa o Grafo do LangGraph
    graph = create_nova_graph()
    final_state = graph.invoke(initial_state)
    
    # Salva no banco de dados se não houver erros fatais no pipeline
    if not final_state.get("errors"):
        try:
            save_comparison_to_db(final_state)
        except Exception as e:
            logging.error(f"Falha ao persistir no banco, continuando resposta: {e}")
            
    return final_state
