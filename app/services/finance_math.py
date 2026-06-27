import numpy as np
import scipy.stats as stats
import numpy_financial as npf
from typing import List, Dict, Any, Union

def calculate_npv(discount_rate: float, cashflows: List[float]) -> float:
    """
    Calcula o Valor Presente Líquido (VPL / NPV) dos fluxos de caixa.
    Fórmula: NPV = sum(CF_t / (1 + r)^t)
    Utiliza numpy_financial.npv.
    """
    if not cashflows:
        return 0.0
    return float(npf.npv(discount_rate, cashflows))

def calculate_irr(cashflows: List[float]) -> float:
    """
    Calcula a Taxa Interna de Retorno (TIR / IRR).
    Caso não convirja, retorna 0.0.
    """
    if not cashflows or len(cashflows) < 2:
        return 0.0
    try:
        val = npf.irr(cashflows)
        if np.isnan(val) or np.isinf(val):
            return 0.0
        return float(val)
    except Exception:
        return 0.0

def calculate_cap_rate(noi: float, property_value: float) -> float:
    """
    Calcula o Cap Rate (Imóveis).
    Cap Rate = NOI / Valor do Imóvel
    """
    if property_value <= 0:
        return 0.0
    return float(noi / property_value)

def calculate_cash_on_cash(annual_cashflow: float, down_payment: float) -> float:
    """
    Calcula o Cash-on-Cash Return.
    Cash-on-Cash = Fluxo de Caixa Anual / Capital Inicial Investido (Down Payment)
    """
    if down_payment <= 0:
        return 0.0
    return float(annual_cashflow / down_payment)

def calculate_real_return(nominal_rate: float, inflation_rate: float) -> float:
    """
    Calcula o Retorno Real Pós-Inflação.
    r_real = (1 + r_nominal) / (1 + i_inflacao) - 1
    """
    return float(((1.0 + nominal_rate) / (1.0 + inflation_rate)) - 1.0)

def calculate_sharpe_ratio(mean_return: float, std_dev: float, risk_free_rate: float) -> float:
    """
    Calcula o Sharpe Ratio simplificado.
    Sharpe = (Retorno Médio - Taxa Livre de Risco) / Desvio Padrão
    """
    if std_dev <= 0.0001:
        return 0.0
    return float((mean_return - risk_free_rate) / std_dev)

def calculate_payback(initial_investment: float, annual_cashflows: List[float], discount_rate: float = 0.0) -> Dict[str, Any]:
    """
    Calcula o período de Payback Simples e Payback Descontado.
    Retorna a quantidade de anos necessária para recuperar o investimento inicial.
    """
    initial_cost = abs(initial_investment)
    
    # Payback Simples
    cumulative_simple = 0.0
    payback_simple = None
    for idx, cf in enumerate(annual_cashflows):
        cumulative_simple += cf
        if cumulative_simple >= initial_cost:
            # Interpolação linear
            prev_cum = cumulative_simple - cf
            needed = initial_cost - prev_cum
            fraction = needed / cf if cf > 0 else 0
            payback_simple = idx + fraction
            break
            
    # Payback Descontado
    cumulative_disc = 0.0
    payback_discounted = None
    for idx, cf in enumerate(annual_cashflows):
        disc_cf = cf / ((1.0 + discount_rate) ** (idx + 1))
        cumulative_disc += disc_cf
        if cumulative_disc >= initial_cost:
            prev_cum = cumulative_disc - disc_cf
            needed = initial_cost - prev_cum
            fraction = needed / disc_cf if disc_cf > 0 else 0
            payback_discounted = idx + fraction
            break

    return {
        "payback_simple": float(payback_simple) if payback_simple is not None else float(len(annual_cashflows)) + 99.0,
        "payback_discounted": float(payback_discounted) if payback_discounted is not None else float(len(annual_cashflows)) + 99.0
    }

def run_monte_carlo(
    asset_type: str,
    initial_investment: float,
    params: Dict[str, Any],
    iterations: int = 1000
) -> Dict[str, Any]:
    """
    Roda simulações estatísticas Monte Carlo de até 2.000 iterações.
    Previne overflow limitando a no máximo 2.000 iterações (conforme regra 9.3 do SDD).
    """
    iterations = min(max(iterations, 100), 2000)
    
    np.random.seed(42) # Seed fixa para determinismo relativo
    
    returns_list = []
    
    # 1. IMÓVEL DE ALUGUEL (REAL ESTATE)
    if asset_type == "real_estate":
        monthly_rent = float(params.get("monthly_rent", 0.0))
        vacancy_mean = float(params.get("vacancy_rate", 0.08)) # ex: 8%
        appreciation_mean = float(params.get("appreciation_rate", 0.04)) # ex: 4%
        opex_pct_mean = float(params.get("opex_rate", 0.35)) # ex: 35%
        
        # Simula por 10 anos (120 meses)
        years = 10
        for _ in range(iterations):
            # Adiciona ruído estatístico a cada simulação
            sim_vacancy = np.clip(np.random.normal(vacancy_mean, 0.04), 0.0, 0.50)
            sim_appreciation = np.random.normal(appreciation_mean, 0.02)
            sim_opex_pct = np.clip(np.random.normal(opex_pct_mean, 0.05), 0.20, 0.60)
            sim_rent_growth = np.random.normal(0.03, 0.015) # inflação dos aluguéis
            
            total_cashflow = 0.0
            current_rent = monthly_rent
            
            # Fluxos anuais
            for yr in range(1, years + 1):
                # Aplica reajuste no aluguel
                if yr > 1:
                    current_rent *= (1.0 + sim_rent_growth)
                
                annual_gross_rent = current_rent * 12.0 * (1.0 - sim_vacancy)
                opex = annual_gross_rent * sim_opex_pct
                noi = annual_gross_rent - opex
                total_cashflow += noi
                
            # Valor final de venda do imóvel corrigido pela valorização
            final_property_value = initial_investment * ((1.0 + sim_appreciation) ** years)
            
            # Retorno total = Dinheiro recebido + valor final do ativo - investimento inicial
            total_net_return = total_cashflow + final_property_value - initial_investment
            annualized_return = (total_cashflow + final_property_value) / initial_investment - 1.0
            # Normaliza para taxa anualizada média
            annual_rate = ((total_cashflow + final_property_value) / initial_investment) ** (1.0 / years) - 1.0
            returns_list.append(annual_rate)

    # 2. RENDA FIXA (FIXED INCOME) OU AÇÕES (EQUITY)
    elif asset_type in ["fixed_income", "equity"]:
        nominal_rate_mean = float(params.get("nominal_rate", 0.08))
        volatility = float(params.get("volatility", 0.02 if asset_type == "fixed_income" else 0.18))
        years = int(params.get("years", 5))
        
        for _ in range(iterations):
            # Modelagem geométrica Browniana simplificada
            annual_returns = np.random.normal(nominal_rate_mean, volatility, years)
            final_multiplier = np.prod(1.0 + annual_returns)
            
            annual_rate = (final_multiplier ** (1.0 / years)) - 1.0
            returns_list.append(annual_rate)

    # 3. PROJETO DE EXPANSÃO (PROJECT)
    elif asset_type == "project":
        cashflows_base = params.get("cashflows", []) # Lista de fluxos anuais (excluindo ano 0)
        discount_rate_mean = float(params.get("discount_rate", 0.10)) # WACC da SME
        years = len(cashflows_base)
        
        # Para projetos comparamos baseados no VPL gerado pela flutuação dos fluxos
        npvs = []
        for _ in range(iterations):
            sim_cashflows = [-abs(initial_investment)]
            for cf in cashflows_base:
                # Variabilidade de 15% de desvio padrão em cada ano
                sim_cf = np.random.normal(cf, abs(cf) * 0.15)
                sim_cashflows.append(sim_cf)
                
            sim_wacc = np.clip(np.random.normal(discount_rate_mean, 0.01), 0.03, 0.25)
            npv_val = calculate_npv(sim_wacc, sim_cashflows)
            npvs.append(npv_val)
            
        # Para projetos, a métrica de retorno simulada será expressa como o NPV gerado dividido pelo investimento inicial
        # para equivaler a um yield comparativo
        returns_list = [v / abs(initial_investment) for v in npvs]
        
    else:
        # Padrão genérico
        for _ in range(iterations):
            returns_list.append(np.random.normal(0.08, 0.04))

    returns_arr = np.array(returns_list)
    
    # Métricas de Percentis
    p10 = float(np.percentile(returns_arr, 10))
    p50 = float(np.percentile(returns_arr, 50))
    p90 = float(np.percentile(returns_arr, 90))
    mean_val = float(np.mean(returns_arr))
    std_dev = float(np.std(returns_arr))
    
    # Probabilidade de perda: retorno nominal/NPV menor que 0 ou retorno negativo
    # Para projetos: fração onde NPV < 0
    if asset_type == "project":
        loss_prob = float(np.sum(np.array(npvs) < 0) / iterations)
    else:
        loss_prob = float(np.sum(returns_arr < 0) / iterations)
        
    return {
        "mean": mean_val,
        "p10": p10,
        "p50": p50,
        "p90": p90,
        "std_dev": std_dev,
        "loss_probability": loss_prob,
        "raw_distribution": [float(v) for v in returns_arr[:100]] # Envia subset de 100 pontos para plotar curva
    }
