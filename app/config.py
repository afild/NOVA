from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # Caminhos base
    BASE_DIR: Path = Path(__file__).parent.parent
    NOVA_DB_PATH: str = "nova_portfolio.db"
    NOVA_DB_PATH: str = "../NOVA/nova_finance.db"   # relativo ao diretório NOVA/
    APEX_DB_PATH: str = "../APEX/apex_ar.db"        # relativo ao diretório NOVA/

    # LLM (Claude via LangChain)
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 4000

    # Servidor FastAPI
    HOST: str = "127.0.0.1"
    PORT: int = 8006
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Parâmetros Financeiros Globais de Fallback
    DEFAULT_RISK_FREE_RATE: float = 0.0525
    DEFAULT_INFLATION_RATE: float = 0.03

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Sobrescreve caminhos e portas com base nas variáveis do SO se fornecidas
if os.environ.get("NOVA_DB_PATH"):
    settings.NOVA_DB_PATH = os.environ.get("NOVA_DB_PATH")
if os.environ.get("NOVA_DB_PATH"):
    settings.NOVA_DB_PATH = os.environ.get("NOVA_DB_PATH")
if os.environ.get("APEX_DB_PATH"):
    settings.APEX_DB_PATH = os.environ.get("APEX_DB_PATH")
if os.environ.get("PORT"):
    settings.PORT = int(os.environ.get("PORT"))
if os.environ.get("HOST"):
    settings.HOST = os.environ.get("HOST")
if os.environ.get("ANTHROPIC_API_KEY"):
    settings.ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
