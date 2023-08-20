import logging
from app.services.market_data import get_ticker_info, get_market_rates
from app.services.finance_math import calculate_real_return

def run_fixed_income_agent(state: dict) -> dict:
    """
    Fixed Income & Equity Agent.
    Calcula retorno líquido real para renda fixa e ações.
    Busca cotações online via yfinance (se ticker especificado) e desconta imposto de renda regressivo
    com base no prazo (term_days) e inflação.
    """
    logging.info("[Fixed Income & Equity Agent] Iniciando processamento de ativos financeiros.")
    
    if "analyzed_assets" not in state:
        state["analyzed_assets"] = []
        
    market_rates = get_market_rates()
    risk_free_rate = market_rates["risk_free_rate"]
    inflation_rate = market_rates["inflation_rate"]
    
    for asset in state.get("assets_data", []):
        if asset.get("type") not in ["fixed_income", "equity"]:
            continue
            
        logging.info(f"[Fixed Income & Equity Agent] Analisando ativo: {asset['name']}")
        meta = asset.get("metadata", {})
        ticker = meta.get("ticker")
        
        # 1. Recupera Taxa Nominal / Rendimento
        nominal_rate = 0.0
        current_price = asset["current_value"]
        
        if ticker:
            # Busca do yfinance se ticker cadastrado
            ticker_data = get_ticker_info(ticker)
            nominal_rate = float(ticker_data["estimated_annual_return"])
            if ticker_data["current_price"] > 0:
                current_price = ticker_data["current_price"]
        else:
            # Título de renda fixa nominal comum
            nominal_rate = float(meta.get("nominal_rate", 0.08)) # taxa padrão
            
        # 2. Imposto de Renda Regressivo (Renda Fixa)
        # Se for renda fixa, aplica tabela regressiva brasileira de IR com base em dias
        # Se for equity, aplica taxa flat (normalmente 15% sobre o ganho de capital)
        ir_rate = 0.15 # padrão
        
        if asset.get("type") == "fixed_income":
            term_days = int(meta.get("term_days", 730)) # assume prazo longo
            if term_days <= 180:
                ir_rate = 0.225
            elif term_days <= 360:
                ir_rate = 0.20
            elif term_days <= 720:
                ir_rate = 0.175
            else:
                ir_rate = 0.15
                
            # Verifica se o título é isento de IR (ex: LCI, LCA, CRI, CRA)
            is_exempt = meta.get("is_exempt", False)
            if is_exempt:
                ir_rate = 0.0
                
        # Calcula taxa líquida pós-IR
        nominal_rate_net = nominal_rate * (1.0 - ir_rate)
        
        # 3. Retorno Líquido Real (descontando inflação)
        real_return = calculate_real_return(nominal_rate_net, inflation_rate)
        
        calculated_metrics = {
            "nominal_rate": nominal_rate,
            "ir_rate": ir_rate,
            "nominal_rate_net": nominal_rate_net,
            "real_return": real_return,
            "current_price": current_price,
            "ticker_checked": bool(ticker),
            "inflation_used": inflation_rate
        }
        
        analyzed_asset = dict(asset)
        analyzed_asset["current_value"] = current_price
        analyzed_asset["calculated_metrics"] = calculated_metrics
        analyzed_asset["estimated_annual_return"] = real_return
        
        state["analyzed_assets"].append(analyzed_asset)
        logging.info(f"[Fixed Income & Equity Agent] Ativo {asset['name']} calculado: Nominal={nominal_rate*100:.2f}%, Real Líquido={real_return*100:.2f}%")
        
    return state
