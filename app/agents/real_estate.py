import logging
from typing import Dict, Any
from app.services.finance_math import calculate_cap_rate, calculate_cash_on_cash

def run_real_estate_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Corporate Standard Docstring: run_real_estate_agent
    Real Estate Rental Agent.
    Calcula Cap Rate, NOI, Cash-on-Cash Return e Gross Yield para ativos do tipo 'real_estate'.
    Aplica fallbacks para preenchimento de campos incompletos.
    """
    logging.info("[Real Estate Agent] Iniciando processamento de ativos imobiliários.")
    
    if "analyzed_assets" not in state:
        state["analyzed_assets"] = []
        
    for asset in state.get("assets_data", []):
        if asset.get("type") != "real_estate":
            continue
            
        logging.info(f"[Real Estate Agent] Analisando imóvel: {asset['name']}")
        meta = asset.get("metadata", {})
        
        # Recupera valores do metadado
        monthly_rent = float(meta.get("monthly_rent", 0.0))
        annual_gross_rent = float(meta.get("annual_gross_rent", monthly_rent * 12.0))
        
        # Down Payment (valor pago inicialmente de capital próprio - se financiado, senão assume o investimento total)
        down_payment = float(meta.get("down_payment", asset["initial_investment"]))
        
        # 1. Regra de Fallback para NOI não informado (Regra 9.1 do SDD)
        noi = meta.get("noi")
        fallback_applied = False
        if noi is None or noi == "":
            # NOI = Aluguel Bruto * 0.65 (taxa padrão de despesas operacionais de 35%)
            noi = annual_gross_rent * 0.65
            fallback_applied = True
            logging.info(f"[Real Estate Agent] NOI não informado. Aplicando fallback de 65% sobre receita bruta ({noi:.2f}).")
        else:
            noi = float(noi)
            
        # 2. Cálculos Financeiros Determinísticos
        cap_rate = calculate_cap_rate(noi, asset["initial_investment"])
        
        # Cash-on-Cash: Fluxo de caixa após despesas e financiamento (se houver)
        # Se houver mortgage_payment no metadado, subtraímos do NOI para achar o fluxo de caixa líquido
        mortgage_payment = float(meta.get("mortgage_payment", 0.0)) * 12.0
        annual_net_cashflow = noi - mortgage_payment
        cash_on_cash = calculate_cash_on_cash(annual_net_cashflow, down_payment)
        
        gross_yield = 0.0
        if asset["initial_investment"] > 0:
            gross_yield = annual_gross_rent / asset["initial_investment"]
            
        # Adiciona métricas calculadas no metadado para persistência temporária na análise
        calculated_metrics = {
            "noi": noi,
            "cap_rate": cap_rate,
            "cash_on_cash": cash_on_cash,
            "gross_yield": gross_yield,
            "annual_gross_rent": annual_gross_rent,
            "down_payment": down_payment,
            "mortgage_payment_annual": mortgage_payment,
            "noi_fallback_applied": fallback_applied
        }
        
        # Clona o ativo e injeta as métricas
        analyzed_asset = dict(asset)
        analyzed_asset["calculated_metrics"] = calculated_metrics
        
        # Estima taxa de retorno média anualizada para o portfólio (gross yield + valorização de 4%)
        appreciation_rate = float(meta.get("appreciation_rate", 0.04))
        analyzed_asset["estimated_annual_return"] = cap_rate + appreciation_rate
        
        state["analyzed_assets"].append(analyzed_asset)
        logging.info(f"[Real Estate Agent] Imóvel {asset['name']} calculado: Cap Rate={cap_rate*100:.2f}%, Cash-on-Cash={cash_on_cash*100:.2f}%")
        
    return state
