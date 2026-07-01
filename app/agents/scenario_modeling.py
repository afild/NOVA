import logging
from typing import Dict, Any
from app.services.finance_math import run_monte_carlo

def run_scenario_modeling_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Corporate Standard Docstring: run_scenario_modeling_agent
    Scenario Modeling Agent.
    Executa a simulação Monte Carlo para cada ativo analisado no estado.
    Armazena métricas estatísticas detalhadas de distribuição de risco (p10, p50, p90, loss_probability).
    """
    logging.info("[Scenario Modeling Agent] Iniciando modelagem de cenários e estresse.")
    
    if "simulations" not in state:
        state["simulations"] = {}
        
    for asset in state.get("analyzed_assets", []):
        asset_id = asset["id"]
        asset_type = asset["type"]
        initial_inv = asset["initial_investment"]
        metrics = asset.get("calculated_metrics", {})
        meta = asset.get("metadata", {})
        
        # Prepara parâmetros específicos para rodar no motor Monte Carlo
        params = {}
        if asset_type == "real_estate":
            params = {
                "monthly_rent": float(meta.get("monthly_rent", 0.0)),
                "vacancy_rate": float(meta.get("vacancy_rate", 0.08)),
                "appreciation_rate": float(meta.get("appreciation_rate", 0.04)),
                "opex_rate": float(meta.get("opex_rate", 0.35))
            }
        elif asset_type in ["fixed_income", "equity"]:
            params = {
                "nominal_rate": float(metrics.get("nominal_rate", 0.08)),
                "volatility": float(metrics.get("volatility", 0.15)),
                "years": int(meta.get("years", 5))
            }
        elif asset_type == "project":
            params = {
                "cashflows": metrics.get("cashflows", []),
                "discount_rate": float(metrics.get("wacc", 0.10))
            }
            
        logging.info(f"[Scenario Modeling Agent] Rodando Monte Carlo para ativo '{asset['name']}' ({asset_type}).")
        
        try:
            # Executa simulação com 1000 iterações (prevenindo lentidão e estouros)
            sim_result = run_monte_carlo(asset_type, initial_inv, params, iterations=1000)
            
            # Formata as chaves de saída para guardar no dicionário de simulação do estado
            state["simulations"][asset_id] = {
                "asset_id": asset_id,
                "asset_name": asset["name"],
                "asset_type": asset_type,
                "mean_return": sim_result["mean"],
                "p10_return": sim_result["p10"],
                "p50_return": sim_result["p50"],
                "p90_return": sim_result["p90"],
                "std_dev": sim_result["std_dev"],
                "loss_probability": sim_result["loss_probability"],
                "raw_distribution": sim_result["raw_distribution"]
            }
            
            logging.info(f"[Scenario Modeling Agent] Monte Carlo para '{asset['name']}' finalizado: P10={sim_result['p10']*100:.2f}%, P90={sim_result['p90']*100:.2f}%")
        except Exception as e:
            err_msg = f"Falha na simulação de Monte Carlo para o ativo {asset['name']}: {str(e)}"
            logging.error(f"[Scenario Modeling Agent] {err_msg}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(err_msg)
            
    return state
