import logging
from fastapi import APIRouter
from app.services.market_data import get_market_rates

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/health")
def health_check():
    """Endpoint de verificação de integridade operacional do sistema NOVA."""
    return {
        "status": "healthy",
        "system": "NOVA (Net Asset & Opportunity Valuation Agent)",
        "version": "0.1.0"
    }

@router.get("/market-rates")
def check_market_rates():
    """Consulta e retorna as taxas de juros (risk-free) e inflação ativas no sistema."""
    try:
        rates = get_market_rates()
        return {
            "status": "success",
            "rates": rates
        }
    except Exception as e:
        logging.error(f"[API System] Erro ao consultar taxas macroeconômicas: {e}")
        return {
            "status": "error",
            "message": "Erro ao carregar taxas. Usando valores estáticos do arquivo de configuração.",
            "rates": {
                "risk_free_rate": 0.0525,
                "inflation_rate": 0.0300
            }
        }
