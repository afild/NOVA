# run.py
import sys
import os
from pathlib import Path
import logging

# Adiciona o diretório atual ao path do Python para permitir importações absolutas de app.
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))

# Carrega variáveis de ambiente antes de qualquer importação interna
env_file = current_dir / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

def check_dependencies():
    """Valida se as dependências fundamentais do NOVA estão instaladas."""
    required = [
        "fastapi", "uvicorn", "sqlalchemy", "pydantic", 
        "langchain", "langgraph", "numpy", "scipy", 
        "numpy_financial", "yfinance", "pandas"
    ]
    missing = []
    for pkg in required:
        try:
            if pkg == "numpy_financial":
                __import__("numpy_financial")
            else:
                __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
            
    if missing:
        print(f"❌ Dependências ausentes: {', '.join(missing)}")
        print("   Por favor execute: pip install -r requirements.txt")
        sys.exit(1)

def ensure_directories():
    """Garante que a estrutura de diretórios para dados e estáticos do frontend exista."""
    frontend_dir = current_dir / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    
    # Garante subdiretórios de dados
    data_dir = current_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Estrutura de diretórios locais verificada.")

def initialize_database():
    """Inicializa o banco SQLite do NOVA (nova_portfolio.db)."""
    from app.database.db_manager import init_db
    init_db()
    print("✅ Banco de dados SQLite NOVA inicializado com sucesso.")

if __name__ == "__main__":
    check_dependencies()
    ensure_directories()
    initialize_database()

    port = int(os.environ.get("PORT", 8006))
    host = os.environ.get("HOST", "127.0.0.1")
    ai_mode = "LLM (Claude via LangChain)" if os.environ.get("ANTHROPIC_API_KEY") else "Offline Heuristic Fallback"

    print("=" * 65)
    print("   NOVA — Net Asset & Opportunity Valuation Agent")
    print("=" * 65)
    print(f"   AI Mode   : {ai_mode}")
    print(f"   Dashboard : http://{host}:{port}/static/index.html")
    print(f"   API Docs  : http://{host}:{port}/docs")
    print("=" * 65)

    import uvicorn
    # reload=False para consistência local de instâncias de base única
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
