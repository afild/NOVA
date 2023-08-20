# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_health_check():
    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "NOVA" in data["system"]

def test_api_crud_workflow():
    # 1. Cria Ativo
    asset_payload = {
        "name": "Fundo Imobiliário Mock",
        "type": "real_estate",
        "initial_investment": 150000.0,
        "current_value": 150000.0,
        "liquidity_type": "medium",
        "risk_level": "medium",
        "metadata": {
            "monthly_rent": 1200.0,
            "vacancy_rate": 0.05,
            "appreciation_rate": 0.03,
            "opex_rate": 0.30
        }
    }
    
    post_res = client.post("/api/assets", json=asset_payload)
    assert post_res.status_code == 201
    created_asset = post_res.json()
    assert created_asset["name"] == "Fundo Imobiliário Mock"
    assert created_asset["initial_investment"] == 150000.0
    asset_id = created_asset["id"]
    
    # 2. Busca Ativo pelo ID
    get_res = client.get(f"/api/assets/{asset_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Fundo Imobiliário Mock"
    
    # 3. Lista Ativos
    list_res = client.get("/api/assets")
    assert list_res.status_code == 200
    assets = list_res.json()
    assert len(assets) >= 1
    assert any(a["id"] == asset_id for a in assets)
    
    # 4. Busca Métricas do Ativo
    metrics_res = client.get(f"/api/assets/{asset_id}/metrics")
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()
    assert metrics_data["asset_id"] == asset_id
    assert "noi" in metrics_data["metrics"]
    assert "cap_rate" in metrics_data["metrics"]
    
    # 5. Roda Simulação de Monte Carlo avulsa
    sim_res = client.post(f"/api/assets/{asset_id}/simulate?iterations=100")
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["asset_id"] == asset_id
    assert "mean" in sim_data["metrics"]
    assert "p10" in sim_data["metrics"]
    
    # 6. Compara Ativos
    # Vamos criar um segundo ativo rápido para ter o que comparar
    asset_payload_2 = {
        "name": "CDB Fictício",
        "type": "fixed_income",
        "initial_investment": 50000.0,
        "current_value": 50000.0,
        "liquidity_type": "high",
        "risk_level": "low",
        "metadata": {
            "nominal_rate": 0.10,
            "term_days": 365,
            "is_exempt": True
        }
    }
    post_res_2 = client.post("/api/assets", json=asset_payload_2)
    assert post_res_2.status_code == 201
    asset_id_2 = post_res_2.json()["id"]
    
    # Executa a comparação
    compare_payload = {
        "query": "Qual oferece maior estabilidade?",
        "asset_ids": [asset_id, asset_id_2],
        "temporary_assets": []
    }
    compare_res = client.post("/api/compare", json=compare_payload)
    assert compare_res.status_code == 200
    compare_data = compare_res.json()
    assert len(compare_data["ranking"]) == 2
    assert "recommendation" in compare_data
    
    # 7. Busca Histórico de Comparação
    history_res = client.get("/api/compare/history")
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 1
    
    # 8. Deleta o Ativo
    del_res = client.delete(f"/api/assets/{asset_id}")
    assert del_res.status_code == 204
    client.delete(f"/api/assets/{asset_id_2}")
    
    # Confirma que foi deletado
    get_res_deleted = client.get(f"/api/assets/{asset_id}")
    assert get_res_deleted.status_code == 404
