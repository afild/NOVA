import logging
from typing import Dict, Any, List

def run_comparative_decision_agent(state: dict) -> dict:
    """
    Comparative Decision Agent.
    Executa uma análise de decisão multicritério (MCDA) comparando todos os ativos avaliados.
    Ajusta dinamicamente os pesos da matriz com base nas intenções detectadas no texto da consulta do usuário.
    """
    logging.info("[Comparative Decision Agent] Iniciando avaliação multicritério.")
    
    if "ranking" not in state:
        state["ranking"] = []
        
    analyzed_assets = state.get("analyzed_assets", [])
    simulations = state.get("simulations", {})
    query = state.get("query", "").lower()
    
    if not analyzed_assets:
        logging.warning("[Comparative Decision Agent] Nenhum ativo analisado disponível para comparação.")
        return state
        
    # 1. Definição Dinâmica de Pesos com base na consulta
    # Padrão balanceado: Retorno (40%), Risco de Perda (30%), Liquidez (20%), Volatilidade/Estabilidade (10%)
    w_return = 0.40
    w_risk = 0.30
    w_liquidity = 0.20
    w_stability = 0.10
    profile_detected = "Equilibrado"
    
    # Detecção simples de palavras-chave para modelar a intenção
    if any(word in query for word in ["seguro", "segurança", "baixo risco", "conservador", "estável", "estabilidade"]):
        w_return = 0.20
        w_risk = 0.50
        w_liquidity = 0.15
        w_stability = 0.15
        profile_detected = "Conservador (Foco em Risco de Perda)"
    elif any(word in query for word in ["liquidez", "resgatar", "curto prazo", "rápido", "disponível"]):
        w_return = 0.20
        w_risk = 0.20
        w_liquidity = 0.50
        w_stability = 0.10
        profile_detected = "Liquidez (Foco em Velocidade de Resgate)"
    elif any(word in query for word in ["retorno", "rendimento", "lucrar", "ganhar", "agressivo", "rentabilidade", "tir"]):
        w_return = 0.60
        w_risk = 0.20
        w_liquidity = 0.10
        w_stability = 0.10
        profile_detected = "Agressivo (Foco em Retorno)"
        
    logging.info(f"[Comparative Decision Agent] Perfil de pesos detectado: {profile_detected}. Pesos: Retorno={w_return}, Risco={w_risk}, Liquidez={w_liquidity}, Estabilidade={w_stability}")
    
    # 2. Computa scores individuais dos ativos (escala 0 a 10)
    scores = []
    for asset in analyzed_assets:
        asset_id = asset["id"]
        sim_data = simulations.get(asset_id, {})
        metrics = asset.get("calculated_metrics", {})
        
        # A. Score de Retorno
        # Estima baseado na taxa esperada (TIR, Cap Rate + valorização, ou rendimento real de RF)
        ret_val = float(asset.get("estimated_annual_return", 0.08))
        # Normaliza: 0% de retorno = score 1; 20% ou mais de retorno = score 10
        score_return = min(max((ret_val / 0.20) * 9.0 + 1.0, 1.0), 10.0)
        
        # B. Score de Risco
        # Baseado na probabilidade de perda (loss_probability) simulada no Monte Carlo
        loss_prob = float(sim_data.get("loss_probability", 0.10))
        # Risco de perda = 0% => score 10; Risco de perda >= 40% => score 1
        score_risk = min(max((1.0 - (loss_prob / 0.40)) * 9.0 + 1.0, 1.0), 10.0)
        
        # C. Score de Liquidez
        # Baseado na categoria de liquidez
        liq_type = asset.get("liquidity_type", "medium")
        if liq_type == "high":
            score_liquidity = 10.0
        elif liq_type == "medium":
            score_liquidity = 5.0
        else:
            score_liquidity = 1.0
            
        # D. Score de Estabilidade / Sharpe Ratio
        # Relação Retorno/Desvio Padrão
        std_dev = float(sim_data.get("std_dev", 0.10))
        if std_dev > 0.0001:
            sharpe = max(0.0, (ret_val - 0.0525) / std_dev) # prêmio sobre treasury yield de 5.25%
        else:
            sharpe = 2.0 # ativo estável sem variabilidade
        # Normaliza Sharpe: 0 = score 1; 3 ou mais = score 10
        score_stability = min(max((sharpe / 3.0) * 9.0 + 1.0, 1.0), 10.0)
        
        # Score final ponderado
        final_score = (
            score_return * w_return +
            score_risk * w_risk +
            score_liquidity * w_liquidity +
            score_stability * w_stability
        )
        
        scores.append({
            "asset_id": asset_id,
            "name": asset["name"],
            "type": asset["type"],
            "score_return": round(score_return, 2),
            "score_risk": round(score_risk, 2),
            "score_liquidity": round(score_liquidity, 2),
            "score_stability": round(score_stability, 2),
            "final_score": round(final_score, 2),
            "estimated_annual_return": round(ret_val, 4),
            "loss_probability": round(loss_prob, 4)
        })
        
    # 3. Classifica o ranking em ordem decrescente do final_score
    scores.sort(key=lambda x: x["final_score"], reverse=True)
    
    state["ranking"] = scores
    logging.info(f"[Comparative Decision Agent] Matriz finalizada. Vencedor: '{scores[0]['name']}' com score {scores[0]['final_score']}.")
    
    return state
