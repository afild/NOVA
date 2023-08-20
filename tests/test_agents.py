# tests/test_agents.py
import pytest
import json
from sqlalchemy import text
from app.database.db_manager import SessionLocal
from app.agents.orchestrator import run_nova_comparison_pipeline

def test_langgraph_pipeline_execution():
    db = SessionLocal()
    
    # 1. Insere ativos de teste no banco SQLite de teste
    meta_real_estate = {
        "monthly_rent": 2500.0,
        "vacancy_rate": 0.05,
        "appreciation_rate": 0.04,
        "opex_rate": 0.30,
        "noi": 28500.0,
        "down_payment": 300000.0
    }
    meta_fixed_income = {
        "nominal_rate": 0.115,
        "term_days": 365,
        "is_exempt": False
    }
    
    try:
        db.execute(
            text("""
                INSERT INTO assets (name, type, initial_investment, current_value, liquidity_type, risk_level, metadata)
                VALUES ('Apartamento 101', 'real_estate', 300000.0, 300000.0, 'low', 'medium', :meta_re)
            """),
            {"meta_re": json.dumps(meta_real_estate)}
        )
        db.execute(
            text("""
                INSERT INTO assets (name, type, initial_investment, current_value, liquidity_type, risk_level, metadata)
                VALUES ('CDB Banco A', 'fixed_income', 100000.0, 100000.0, 'high', 'low', :meta_fi)
            """),
            {"meta_fi": json.dumps(meta_fixed_income)}
        )
        db.commit()
        
        # Recupera os IDs inseridos
        result = db.execute(text("SELECT id FROM assets ORDER BY id DESC LIMIT 2")).fetchall()
        asset_ids = [row[0] for row in result]
        
        # 2. Executa a pipeline de comparação do LangGraph
        query = "Qual dessas opções é melhor sob o ponto de vista do risco e retorno?"
        final_state = run_nova_comparison_pipeline(
            query=query,
            asset_ids=asset_ids,
            temporary_assets=[]
        )
        
        # 3. Validações
        assert not final_state.get("errors"), f"Erros na pipeline: {final_state.get('errors')}"
        assert len(final_state["assets_data"]) == 2
        assert len(final_state["analyzed_assets"]) == 2
        assert len(final_state["simulations"]) == 2
        assert len(final_state["ranking"]) == 2
        
        # O ranking deve estar ordenado
        assert final_state["ranking"][0]["final_score"] >= final_state["ranking"][1]["final_score"]
        
        # A recomendação qualitativa deve ter sido preenchida (modo fallback ou claude)
        assert len(final_state["recommendation"]) > 100
        assert "Relatório de Avaliação" in final_state["recommendation"] or "NOVA" in final_state["recommendation"]
        
        # Verifica se o histórico foi salvo na tabela comparison_history do SQLite
        history = db.execute(text("SELECT id, query_text, compared_asset_ids, ranking_json FROM comparison_history ORDER BY id DESC LIMIT 1")).fetchone()
        assert history is not None
        assert history[1] == query
        assert str(asset_ids[0]) in history[2]
        
    finally:
        db.close()
