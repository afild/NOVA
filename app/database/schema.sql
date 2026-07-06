-- app/database/schema.sql

CREATE TABLE IF NOT EXISTS assets (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    type                TEXT NOT NULL, -- real_estate | fixed_income | equity | project
    initial_investment  REAL NOT NULL, -- valor do investimento inicial necessário
    current_value       REAL NOT NULL, -- valor marcado a mercado ou valor atualizado
    liquidity_type      TEXT DEFAULT 'medium', -- high | medium | low
    risk_level          TEXT DEFAULT 'medium', -- low | medium | high
    metadata            TEXT NOT NULL, -- JSON string contendo atributos específicos (ex: NOI, fluxos de caixa, tickers, rentabilidade pactuada)
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comparison_history (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text          TEXT NOT NULL, -- pergunta original do usuário
    compared_asset_ids  TEXT NOT NULL, -- string formatada ex: "1,2,5"
    ranking_json        TEXT NOT NULL, -- JSON com o ranking gerado pelo Comparative Agent
    advisor_narrative   TEXT NOT NULL, -- texto explicativo do AI Advisor Agent
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulation_results (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id            INTEGER REFERENCES assets(id),
    simulation_type     TEXT NOT NULL, -- monte_carlo | stress_test
    parameters_json     TEXT NOT NULL, -- parâmetros usados (ex: juros_base, vacancia_media)
    metrics_json        TEXT NOT NULL, -- resultados (ex: p10, p50, p90 de retorno, probabilidade de perda)
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
