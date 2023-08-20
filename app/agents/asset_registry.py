import json
import logging
from typing import Dict, Any, List
from sqlalchemy import text
from app.database.db_manager import engine

def run_asset_registry(state: dict) -> dict:
    """
    Asset Registry Agent.
    Recupera ativos persistidos no banco de dados SQLite com base nos ids fornecidos.
    Se o payload contiver 'temporary_assets' (oportunidades passadas dinamicamente no request),
    ele também os adiciona na lista para a análise concorrente.
    """
    logging.info("[Asset Registry] Iniciando validação e carregamento de ativos.")
    
    # Inicializa campos de segurança do estado
    if "assets_data" not in state:
        state["assets_data"] = []
    if "errors" not in state:
        state["errors"] = []
        
    asset_ids = state.get("asset_ids", [])
    
    # 1. Recupera do Banco de Dados SQLite
    if asset_ids:
        try:
            with engine.connect() as connection:
                # Transforma lista de IDs em string segura para o IN do SQL
                ids_str = ",".join([str(int(i)) for i in asset_ids])
                query = text(f"SELECT id, name, type, initial_investment, current_value, liquidity_type, risk_level, metadata FROM assets WHERE id IN ({ids_str})")
                result = connection.execute(query)
                
                for row in result:
                    # Cada registro é transformado em dict
                    asset = {
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "initial_investment": float(row[3]),
                        "current_value": float(row[4]),
                        "liquidity_type": row[5],
                        "risk_level": row[6],
                        "metadata": {}
                    }
                    try:
                        # Desserializa os metadados específicos salvos como JSON string
                        if row[7]:
                            asset["metadata"] = json.loads(row[7])
                    except Exception as json_err:
                        logging.error(f"[Asset Registry] Erro ao decodificar metadata do ativo {row[0]}: {json_err}")
                        asset["metadata"] = {}
                        
                    state["assets_data"].append(asset)
            logging.info(f"[Asset Registry] {len(state['assets_data'])} ativos carregados do banco SQLite.")
        except Exception as e:
            err_msg = f"Erro no carregamento de ativos do banco: {str(e)}"
            logging.error(f"[Asset Registry] {err_msg}")
            state["errors"].append(err_msg)
            
    # 2. Processa ativos temporários/virtuais se fornecidos pelo usuário no request/pergunta
    temporary_assets = state.get("temporary_assets", [])
    if temporary_assets:
        for idx, temp in enumerate(temporary_assets):
            # Garante que ativos temporários tenham estrutura mínima validada
            # Damos IDs negativos para diferenciar de ativos reais persistidos
            temp_id = -(idx + 1)
            temp_asset = {
                "id": temp_id,
                "name": temp.get("name", f"Oportunidade Temporária #{idx + 1}"),
                "type": temp.get("type", "project"),
                "initial_investment": float(temp.get("initial_investment", 0.0)),
                "current_value": float(temp.get("current_value", temp.get("initial_investment", 0.0))),
                "liquidity_type": temp.get("liquidity_type", "medium"),
                "risk_level": temp.get("risk_level", "medium"),
                "metadata": temp.get("metadata", {}),
                "is_temporary": True
            }
            state["assets_data"].append(temp_asset)
            logging.info(f"[Asset Registry] Oportunidade temporária adicionada: {temp_asset['name']}")

    if not state["assets_data"]:
        state["errors"].append("Nenhum ativo ou oportunidade foi fornecido para análise.")
        
    return state
