# tests/test_math.py
import pytest
from app.services.finance_math import (
    calculate_npv,
    calculate_irr,
    calculate_cap_rate,
    calculate_cash_on_cash,
    calculate_real_return,
    calculate_payback,
    run_monte_carlo
)

def test_calculate_npv():
    # Teste de VPL com taxa de 10% e investimento de -100, com fluxos de 50 e 60
    # NPV = -100 + 50/1.1 + 60/1.21 = -100 + 45.4545 + 49.5867 = -4.9587
    discount_rate = 0.10
    cashflows = [-100.0, 50.0, 60.0]
    npv = calculate_npv(discount_rate, cashflows)
    assert round(npv, 4) == -4.9587

def test_calculate_irr():
    # Teste de TIR com investimento de -100, seguido por 60 e 60
    # A TIR deve ser aproximadamente 13.0662% (0.1307)
    cashflows = [-100.0, 60.0, 60.0]
    irr = calculate_irr(cashflows)
    assert round(irr, 4) == 0.1307

def test_calculate_cap_rate():
    noi = 15000.0
    property_value = 200000.0
    cap_rate = calculate_cap_rate(noi, property_value)
    assert cap_rate == 0.075  # 7.5%

def test_calculate_cash_on_cash():
    annual_cashflow = 12000.0
    down_payment = 50000.0
    coc = calculate_cash_on_cash(annual_cashflow, down_payment)
    assert coc == 0.24  # 24%

def test_calculate_real_return():
    nominal_rate = 0.115
    inflation_rate = 0.03
    # real_return = (1 + 0.115) / (1 + 0.03) - 1 = 1.115 / 1.03 - 1 = 0.082524 (8.25%)
    r_real = calculate_real_return(nominal_rate, inflation_rate)
    assert round(r_real, 6) == 0.082524

def test_calculate_payback():
    initial_investment = 100.0
    cashflows = [30.0, 40.0, 50.0, 30.0]
    # Acumulado: Ano 1 = 30, Ano 2 = 70, Ano 3 = 120. Recupera no Ano 3.
    # Excesso necessário no ano 3: (100 - 70) / 50 = 30 / 50 = 0.6 anos.
    # Payback simples: 2.6 anos
    res = calculate_payback(initial_investment, cashflows, discount_rate=0.10)
    assert round(res["payback_simple"], 1) == 2.6
    assert res["payback_discounted"] > 2.6  # Payback descontado demora mais

def test_run_monte_carlo():
    # Testa simulação Monte Carlo para real_estate
    params = {
        "monthly_rent": 2000.0,
        "vacancy_rate": 0.08,
        "appreciation_rate": 0.04,
        "opex_rate": 0.35
    }
    res = run_monte_carlo("real_estate", 150000.0, params, iterations=100)
    
    assert "mean" in res
    assert "p10" in res
    assert "p90" in res
    assert "loss_probability" in res
    assert len(res["raw_distribution"]) > 0
    assert 0.0 <= res["loss_probability"] <= 1.0
