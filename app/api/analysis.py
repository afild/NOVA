import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.db_manager import get_db
from app.services.finance_math import run_monte_carlo, calculate_cap_rate, calculate_cash_on_cash, calculate_npv, calculate_irr, calculate_payback, calculate_real_return
from app.services.market_data import get_market_rates

router = APIRouter(prefix="/assets", tags=["Analysis"])

@router.post("/{id}/simulate")
def simulate_asset(id: int, iterations: int = 1000, db: Session = Depends(get_db)):
    """
    Roda simulação estatística Monte Carlo de forma avulsa para o ativo especificado pelo ID.
    Salva os resultados estatísticos gerados no SQLite.
    """
    try:
        # 1. Recupera o ativo do banco de dados
        result = db.execute(
            text("SELECT id, name, type, initial_investment, metadata FROM assets WHERE id = :id"),
            {"id": id}
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ativo não encontrado.")
            
        asset_id, name, asset_type, initial_investment, metadata_str = row
        meta = {}
        if metadata_str:
            meta = json.loads(metadata_str)
            
        # 2. Configura parâmetros de simulação por tipo de ativo
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
                "nominal_rate": float(meta.get("nominal_rate", 0.08)),
                "volatility": float(meta.get("volatility", 0.15)),
                "years": int(meta.get("years", 5))
            }
        elif asset_type == "project":
            cashflows = meta.get("cashflows", [])
            if not cashflows:
                cashflows = [initial_investment * 0.25] * 5
            params = {
                "cashflows": [float(cf) for cf in cashflows],
                "discount_rate": float(meta.get("wacc", 0.10))
            }
            
        # 3. Executa Monte Carlo
        sim_result = run_monte_carlo(asset_type, float(initial_investment), params, iterations=iterations)
        
        # 4. Salva o resultado no banco de dados SQLite
        db_params = {"asset_type": asset_type, "iterations": iterations, **params}
        db_metrics = {
            "p10": sim_result["p10"],
            "p50": sim_result["p50"],
            "p90": sim_result["p90"],
            "mean": sim_result["mean"],
            "std_dev": sim_result["std_dev"],
            "loss_probability": sim_result["loss_probability"]
        }
        
        db.execute(
            text("""
                INSERT INTO simulation_results (asset_id, simulation_type, parameters_json, metrics_json)
                VALUES (:asset_id, 'monte_carlo', :params_json, :metrics_json)
            """),
            {
                "asset_id": asset_id,
                "params_json": json.dumps(db_params),
                "metrics_json": json.dumps(db_metrics)
            }
        )
        db.commit()
        
        return {
            "asset_id": asset_id,
            "asset_name": name,
            "simulation_type": "monte_carlo",
            "metrics": sim_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"[API Analysis] Erro na simulação do ativo {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao executar a simulação.")

@router.get("/{id}/metrics")
def get_asset_metrics(id: int, db: Session = Depends(get_db)):
    """Calcula e retorna as métricas financeiras brutas e determinísticas do ativo com base em suas regras de negócio."""
    try:
        result = db.execute(
            text("SELECT id, name, type, initial_investment, current_value, metadata FROM assets WHERE id = :id"),
            {"id": id}
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ativo não encontrado.")
            
        asset_id, name, asset_type, initial_inv, current_val, metadata_str = row
        meta = {}
        if metadata_str:
            meta = json.loads(metadata_str)
            
        market_rates = get_market_rates()
        inflation_rate = market_rates["inflation_rate"]
        
        metrics = {}
        
        if asset_type == "real_estate":
            monthly_rent = float(meta.get("monthly_rent", 0.0))
            annual_gross_rent = float(meta.get("annual_gross_rent", monthly_rent * 12.0))
            down_payment = float(meta.get("down_payment", initial_inv))
            mortgage_payment = float(meta.get("mortgage_payment", 0.0)) * 12.0
            
            noi = meta.get("noi")
            if noi is None or noi == "":
                noi = annual_gross_rent * 0.65
            else:
                noi = float(noi)
                
            cap_rate = calculate_cap_rate(noi, initial_inv)
            cash_on_cash = calculate_cash_on_cash(noi - mortgage_payment, down_payment)
            
            metrics = {
                "noi": noi,
                "cap_rate": cap_rate,
                "cash_on_cash": cash_on_cash,
                "annual_gross_rent": annual_gross_rent,
                "down_payment": down_payment
            }
            
        elif asset_type in ["fixed_income", "equity"]:
            nominal_rate = float(meta.get("nominal_rate", 0.08))
            ir_rate = 0.15
            if asset_type == "fixed_income":
                term_days = int(meta.get("term_days", 730))
                if term_days <= 180:
                    ir_rate = 0.225
                elif term_days <= 360:
                    ir_rate = 0.20
                elif term_days <= 720:
                    ir_rate = 0.175
                else:
                    ir_rate = 0.15
                if meta.get("is_exempt", False):
                    ir_rate = 0.0
                    
            nominal_rate_net = nominal_rate * (1.0 - ir_rate)
            real_return = calculate_real_return(nominal_rate_net, inflation_rate)
            
            metrics = {
                "nominal_rate": nominal_rate,
                "ir_rate": ir_rate,
                "nominal_rate_net": nominal_rate_net,
                "real_return": real_return
            }
            
        elif asset_type == "project":
            cashflows = meta.get("cashflows", [])
            if not cashflows:
                cashflows = [initial_inv * 0.25] * 5
            cashflows = [float(cf) for cf in cashflows]
            
            wacc = float(meta.get("wacc") or (market_rates["risk_free_rate"] + 0.0675))
            full_cashflows = [-abs(initial_inv)] + cashflows
            
            npv = calculate_npv(wacc, full_cashflows)
            irr = calculate_irr(full_cashflows)
            payback = calculate_payback(initial_inv, cashflows, wacc)
            
            metrics = {
                "wacc": wacc,
                "npv": npv,
                "irr": irr,
                "payback_simple": payback["payback_simple"],
                "payback_discounted": payback["payback_discounted"]
            }
            
        return {
            "asset_id": asset_id,
            "asset_name": name,
            "asset_type": asset_type,
            "metrics": metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[API Analysis] Erro ao carregar métricas para ativo {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao calcular as métricas.")
