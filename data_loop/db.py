from __future__ import annotations

from pathlib import Path

from experiment_loop.db import init_db as init_experiment_db
from research_loop.db import connect


SCHEMA = """
CREATE TABLE IF NOT EXISTS data_jobs (
    job_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    data_name TEXT NOT NULL,
    dataset_type TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'binance_usdm',
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL DEFAULT '1h',
    status TEXT NOT NULL DEFAULT 'pending',
    dataset_id TEXT,
    error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id) REFERENCES experiment_specs(experiment_id),
    FOREIGN KEY (requirement_id) REFERENCES experiment_data_requirements(requirement_id),
    UNIQUE(experiment_id, data_name, provider, symbol, interval)
);

CREATE INDEX IF NOT EXISTS idx_data_jobs_status
ON data_jobs(status);

CREATE INDEX IF NOT EXISTS idx_data_jobs_experiment
ON data_jobs(experiment_id);

CREATE TABLE IF NOT EXISTS market_datasets (
    dataset_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    dataset_type TEXT NOT NULL,
    provider TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL DEFAULT '',
    path TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    start_at TEXT NOT NULL DEFAULT '',
    end_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'available',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id) REFERENCES experiment_specs(experiment_id),
    UNIQUE(experiment_id, dataset_type, provider, symbol, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_market_datasets_experiment
ON market_datasets(experiment_id);
"""


def init_db(db_path: Path | str) -> None:
    init_experiment_db(db_path)
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)

