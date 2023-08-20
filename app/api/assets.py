import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from app.database.db_manager import get_db

router = APIRouter(prefix="/assets", tags=["Assets"])

class AssetCreate(BaseModel):
    name: str
    type: str  # real_estate | fixed_income | equity | project
    initial_investment: float
    current_value: float
    liquidity_type: str = "medium"  # high | medium | low
    risk_level: str = "medium"      # low | medium | high
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AssetResponse(BaseModel):
    id: int
    name: str
    type: str
    initial_investment: float
    current_value: float
    liquidity_type: str
    risk_level: str
    metadata: Dict[str, Any]
    created_at: str

@router.get("", response_model=List[AssetResponse])
def list_assets(db: Session = Depends(get_db)):
    """Lista todos os ativos cadastrados no portfólio."""
    try:
        result = db.execute(text("SELECT id, name, type, initial_investment, current_value, liquidity_type, risk_level, metadata, created_at FROM assets ORDER BY id DESC"))
        assets = []
        for row in result:
            meta = {}
            if row[7]:
                try:
                    meta = json.loads(row[7])
                except Exception:
                    meta = {}
            assets.append({
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "initial_investment": float(row[3]),
                "current_value": float(row[4]),
                "liquidity_type": row[5],
                "risk_level": row[6],
                "metadata": meta,
                "created_at": str(row[8])
            })
        return assets
    except Exception as e:
        logging.error(f"[API Assets] Erro ao listar ativos: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar ativos.")

@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    """Cria um novo ativo e persiste no banco SQLite."""
    try:
        metadata_str = json.dumps(asset.metadata, ensure_ascii=False)
        result = db.execute(
            text("""
                INSERT INTO assets (name, type, initial_investment, current_value, liquidity_type, risk_level, metadata)
                VALUES (:name, :type, :initial_investment, :current_value, :liquidity_type, :risk_level, :metadata)
                RETURNING id, created_at
            """),
            {
                "name": asset.name,
                "type": asset.type,
                "initial_investment": asset.initial_investment,
                "current_value": asset.current_value,
                "liquidity_type": asset.liquidity_type,
                "risk_level": asset.risk_level,
                "metadata": metadata_str
            }
        )
        row = result.fetchone()
        db.commit()
        
        if not row:
            raise HTTPException(status_code=500, detail="Falha ao inserir ativo no banco.")
            
        return {
            "id": row[0],
            "name": asset.name,
            "type": asset.type,
            "initial_investment": asset.initial_investment,
            "current_value": asset.current_value,
            "liquidity_type": asset.liquidity_type,
            "risk_level": asset.risk_level,
            "metadata": asset.metadata,
            "created_at": str(row[1])
        }
    except Exception as e:
        db.rollback()
        logging.error(f"[API Assets] Erro ao cadastrar ativo: {e}")
        raise HTTPException(status_code=400, detail=f"Parâmetros de cadastro inválidos: {str(e)}")

@router.get("/{id}", response_model=AssetResponse)
def get_asset(id: int, db: Session = Depends(get_db)):
    """Retorna detalhes de um ativo específico pelo seu ID."""
    try:
        result = db.execute(
            text("SELECT id, name, type, initial_investment, current_value, liquidity_type, risk_level, metadata, created_at FROM assets WHERE id = :id"),
            {"id": id}
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ativo não encontrado.")
            
        meta = {}
        if row[7]:
            try:
                meta = json.loads(row[7])
            except Exception:
                meta = {}
                
        return {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "initial_investment": float(row[3]),
            "current_value": float(row[4]),
            "liquidity_type": row[5],
            "risk_level": row[6],
            "metadata": meta,
            "created_at": str(row[8])
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[API Assets] Erro ao obter ativo {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar detalhes do ativo.")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(id: int, db: Session = Depends(get_db)):
    """Exclui o ativo com base no ID."""
    try:
        # Verifica se existe antes de excluir
        check = db.execute(text("SELECT id FROM assets WHERE id = :id"), {"id": id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Ativo não encontrado.")
            
        db.execute(text("DELETE FROM assets WHERE id = :id"), {"id": id})
        db.execute(text("DELETE FROM simulation_results WHERE asset_id = :id"), {"id": id})
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"[API Assets] Erro ao deletar ativo {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao tentar remover o ativo.")
