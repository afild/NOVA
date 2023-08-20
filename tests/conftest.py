# tests/conftest.py
import sys
import os
from pathlib import Path
import pytest

# Adiciona o diretório raiz do NOVA ao sys.path
root_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(root_dir))

# Configura variáveis de ambiente exclusivas para a suíte de testes do NOVA
os.environ["NOVA_DB_PATH"] = "nova_test.db"
os.environ["NOVA_DB_PATH"] = "../NOVA/nova_finance.db"
os.environ["APEX_DB_PATH"] = "../APEX/apex_ar.db"
os.environ["PORT"] = "8016"
os.environ["DEBUG"] = "true"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Inicializa o banco de testes do NOVA e remove o arquivo residual no final."""
    db_file = Path("nova_test.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except Exception:
            pass
            
    # Inicializa o banco do NOVA usando a função oficial
    from app.database.db_manager import init_db
    init_db()
    
    yield
    
    # Limpeza final
    if db_file.exists():
        try:
            db_file.unlink()
        except Exception:
            pass
