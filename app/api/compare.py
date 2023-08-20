import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from app.database.db_manager import get_db
from app.agents.orchestrator import run_nova_comparison_pipeline

router = APIRouter(prefix="/compare", tags=["Compare"])

class CompareRequest(BaseModel):
    query: str
    asset_ids: List[int] = Field(default_factory=list)
    temporary_assets: List[Dict[str, Any]] = Field(default_factory=list)

@router.post("")
def execute_comparison(payload: CompareRequest):
    """
    Executa a comparação multi-agente utilizando LangGraph.
    Coleta os ativos salvos e/ou temporários, roda as simulações Monte Carlo paralela/sequencialmente,
    computa o ranking de utilidade multicritério e gera a narrativa de recomendação do Advisor.
    """
    if not payload.asset_ids and not payload.temporary_assets:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer ao menos um ID de ativo ou uma oportunidade temporária para comparação."
        )
        
    try:
        logging.info(f"[API Compare] Iniciando pipeline de comparação para a consulta: '{payload.query}'")
        
        # Roda a pipeline do LangGraph
        result_state = run_nova_comparison_pipeline(
            query=payload.query,
            asset_ids=payload.asset_ids,
            temporary_assets=payload.temporary_assets
        )
        
        # Se ocorreram erros fatais ao rodar o grafo de estados
        if result_state.get("errors"):
            logging.error(f"[API Compare] Pipeline finalizou com erros: {result_state['errors']}")
            raise HTTPException(
                status_code=500,
                detail=f"Erros encontrados durante o processamento do pipeline: {', '.join(result_state['errors'])}"
            )
            
        # Limpa o raw_distribution do retorno da API para economizar banda (enviamos apenas uma amostra reduzida)
        cleaned_simulations = {}
        for k, v in result_state.get("simulations", {}).items():
            cleaned_sim = dict(v)
            # Mantém apenas os primeiros 50 pontos para plotagem leve
            if "raw_distribution" in cleaned_sim:
                cleaned_sim["raw_distribution"] = cleaned_sim["raw_distribution"][:50]
            cleaned_simulations[k] = cleaned_sim
            
        return {
            "query": result_state.get("query"),
            "ranking": result_state.get("ranking"),
            "simulations": cleaned_simulations,
            "recommendation": result_state.get("recommendation")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[API Compare] Falha geral no pipeline de comparação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno de execução do pipeline: {str(e)}")

@router.get("/history")
def get_comparison_history(limit: int = 10, db: Session = Depends(get_db)):
    """Retorna as últimas análises comparativas e pareceres históricos salvos no SQLite."""
    try:
        result = db.execute(
            text("""
                SELECT id, query_text, compared_asset_ids, ranking_json, advisor_narrative, created_at 
                FROM comparison_history 
                ORDER BY id DESC 
                LIMIT :limit
            """),
            {"limit": limit}
        )
        
        history = []
        for row in result:
            ranking = []
            if row[3]:
                try:
                    ranking = json.loads(row[3])
                except Exception:
                    ranking = []
            history.append({
                "id": row[0],
                "query": row[1],
                "compared_asset_ids": row[2],
                "ranking": ranking,
                "recommendation": row[4],
                "created_at": str(row[5])
            })
        return history
    except Exception as e:
        logging.error(f"[API Compare] Erro ao carregar histórico: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao consultar o histórico.")
