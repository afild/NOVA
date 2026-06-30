import logging
from typing import Dict, Any
from app.services.finance_math import calculate_npv, calculate_irr, calculate_payback
from app.services.market_data import get_market_rates

def run_project_viability_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Corporate Standard Docstring: run_project_viability_agent
    Project Viability Agent.
    Analisa a viabilidade financeira de projetos operacionais/corporativos.
    Calcula NPV, IRR e Payback (simples e descontado) com base na taxa de atratividade (WACC).
    """
    logging.info("[Project Viability Agent] Iniciando processamento de projetos de expansão.")
    
    if "analyzed_assets" not in state:
        state["analyzed_assets"] = []
        
    market_rates = get_market_rates()
    risk_free_rate = market_rates["risk_free_rate"]
    
    for asset in state.get("assets_data", []):
        if asset.get("type") != "project":
            continue
            
        logging.info(f"[Project Viability Agent] Analisando viabilidade do projeto: {asset['name']}")
        meta = asset.get("metadata", {})
        
        # Recupera fluxos de caixa futuros. Ex: [30000, 40000, 45000, 50000]
        cashflows_raw = meta.get("cashflows", [])
        if not cashflows_raw:
            # Se não houver fluxos informados, assume um retorno uniforme linear de 5 anos igual a 25% do investimento anual
            years = 5
            cashflows_raw = [asset["initial_investment"] * 0.25] * years
            logging.info(f"[Project Viability Agent] Sem fluxos informados. Assumindo fluxo uniforme estimado de 5 anos ({cashflows_raw[0]:.2f}/ano).")
            
        # Garante floats na lista de fluxos
        cashflows_raw = [float(v) for v in cashflows_raw]
        
        # O fluxo de caixa no instante 0 é o investimento inicial negativo
        initial_inv = float(asset["initial_investment"])
        full_cashflows = [-abs(initial_inv)] + cashflows_raw
        
        # WACC (Custo Médio Ponderado de Capital)
        # Se não informado, assume Taxa Livre de Risco + prêmio de risco corporativo de 6.75%
        wacc = meta.get("wacc") or meta.get("discount_rate")
        if wacc is None or wacc == "":
            wacc = risk_free_rate + 0.0675
            logging.info(f"[Project Viability Agent] WACC não informado. Arbitrado como Risk-Free + 6.75% = {wacc*100:.2f}%.")
        else:
            wacc = float(wacc)
            
        # 2. Cálculos Financeiros Determinísticos
        npv = calculate_npv(wacc, full_cashflows)
        irr = calculate_irr(full_cashflows)
        
        # Payback
        payback_results = calculate_payback(initial_inv, cashflows_raw, wacc)
        
        calculated_metrics = {
            "wacc": wacc,
            "npv": npv,
            "irr": irr,
            "payback_simple": payback_results["payback_simple"],
            "payback_discounted": payback_results["payback_discounted"],
            "cashflows": cashflows_raw
        }
        
        analyzed_asset = dict(asset)
        analyzed_asset["calculated_metrics"] = calculated_metrics
        # O retorno anualizado estimado do projeto para comparação será a sua TIR
        analyzed_asset["estimated_annual_return"] = irr
        
        state["analyzed_assets"].append(analyzed_asset)
        logging.info(f"[Project Viability Agent] Projeto {asset['name']} calculado: NPV={npv:.2f}, IRR={irr*100:.2f}%, Payback={payback_results['payback_discounted']:.2f} anos")
        
    return state
