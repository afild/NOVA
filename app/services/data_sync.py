import logging
import random
from datetime import datetime, timedelta

def sync_bank_transactions(account_id: str):
    """
    Simula integração com 'outras plataformas' bancárias.
    Retorna uma lista de transações mockadas dos últimos 30 dias.
    """
    logging.info(f"[Data Sync] Sincronizando dados bancários para a conta {account_id}...")
    
    # Mock data for demonstration
    transactions = []
    base_date = datetime.now()
    
    for i in range(10):
        # Transações de entrada (receita)
        transactions.append({
            "id": f"txn_in_{i}",
            "amount": round(random.uniform(5000.0, 15000.0), 2),
            "date": (base_date - timedelta(days=random.randint(1, 30))).isoformat(),
            "category": "sales_revenue",
            "type": "credit"
        })
        
        # Transações de saída (despesa)
        transactions.append({
            "id": f"txn_out_{i}",
            "amount": round(random.uniform(1000.0, 5000.0), 2),
            "date": (base_date - timedelta(days=random.randint(1, 30))).isoformat(),
            "category": "operating_expense",
            "type": "debit"
        })
        
    logging.info("[Data Sync] Sincronização concluída com sucesso.")
    return transactions

def sync_accounting_balance(company_id: str):
    """
    Simula integração com 'outras plataformas' de contabilidade.
    Retorna um resumo de balanço patrimonial mockado.
    """
    logging.info(f"[Data Sync] Sincronizando balanço patrimonial para a empresa {company_id}...")
    
    balance_sheet = {
        "total_assets": round(random.uniform(500000.0, 2000000.0), 2),
        "total_liabilities": round(random.uniform(100000.0, 500000.0), 2),
        "equity": 0.0,
        "last_updated": datetime.now().isoformat()
    }
    balance_sheet["equity"] = balance_sheet["total_assets"] - balance_sheet["total_liabilities"]
    
    logging.info("[Data Sync] Balanço patrimonial sincronizado.")
    return balance_sheet
