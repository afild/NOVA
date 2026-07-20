import logging
from typing import Dict, Any, List

def run_capital_matchmaker(npv: float, irr: float) -> List[Dict[str, Any]]:
    """
    Agente que cruza os resultados de valuation com opções de captação (Mock).
    Não menciona nomes de plataformas governamentais ou privadas reais diretamente,
    usando termos genéricos (ex: 'Programa Federal de Crédito').
    """
    logging.info("[Capital Matchmaker] Cruzando metrics de valuation com perfis de crédito...")
    
    matches = []
    
    if npv > 500000 and irr > 0.15:
        matches.append({
            "program_name": "Programa Federal de Expansão (Tier 1)",
            "max_amount": round(npv * 0.3, 2),
            "interest_rate": "6.5% a.a.",
            "match_score": "High"
        })
    elif npv > 100000:
        matches.append({
            "program_name": "Linha de Crédito para Capital de Giro",
            "max_amount": 100000.0,
            "interest_rate": "8.0% a.a.",
            "match_score": "Medium"
        })
        
    matches.append({
        "program_name": "Fundo de Private Equity Regional",
        "max_amount": round(npv * 0.5, 2),
        "interest_rate": "Equity (10-15%)",
        "match_score": "Medium" if irr > 0.20 else "Low"
    })
    
    return matches
