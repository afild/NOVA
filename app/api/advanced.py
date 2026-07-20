from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.db_manager import get_db
from app.services.export_engine import generate_pitch_deck_html
from app.agents.capital_matchmaker import run_capital_matchmaker
import json
import logging

router = APIRouter(tags=["Advanced Features"])

@router.get("/export/{asset_id}", response_class=HTMLResponse)
def export_asset_pitch(asset_id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(
            text("SELECT id, name, current_value FROM assets WHERE id = :id"),
            {"id": asset_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Ativo não encontrado.")
            
        asset_data = {
            "name": result[1],
            "current_value": float(result[2])
        }
        
        # Mock narrative
        narrative = f"Based on the asset {asset_data['name']} valuation, it represents a stable investment."
        
        html_content = generate_pitch_deck_html(asset_data, narrative)
        return html_content
    except Exception as e:
        logging.error(f"[API Export] Erro ao exportar ativo {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao gerar documento.")

@router.post("/matchmake/{asset_id}")
def matchmake_asset(asset_id: int, db: Session = Depends(get_db)):
    try:
        # Puxa o NPv/IRR simulado se tiver
        result = db.execute(
            text("SELECT metrics_json FROM simulation_results WHERE asset_id = :id ORDER BY id DESC LIMIT 1"),
            {"id": asset_id}
        ).fetchone()
        
        npv = 0.0
        irr = 0.0
        if result and result[0]:
            metrics = json.loads(result[0])
            npv = metrics.get("mean", 150000.0) # mock fallback
            irr = 0.18 # mock
            
        matches = run_capital_matchmaker(npv, irr)
        return {"asset_id": asset_id, "matches": matches}
        
    except Exception as e:
        logging.error(f"[API Matchmake] Erro: {e}")
        raise HTTPException(status_code=500, detail="Erro interno.")
