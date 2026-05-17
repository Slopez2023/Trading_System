from __future__ import annotations

from pathlib import Path

from research_loop.db import connect, init_db as init_research_db


SCHEMA = """
CREATE TABLE IF NOT EXISTS experiment_specs (
    experiment_id TEXT PRIMARY KEY,
    source_record_id TEXT NOT NULL,
    thesis TEXT NOT NULL,
    experiment_type TEXT NOT NULL,
    market TEXT NOT NULL DEFAULT '',
    asset TEXT NOT NULL DEFAULT '',
    timeframes_json TEXT NOT NULL DEFAULT '[]',
    data_needed_json TEXT NOT NULL DEFAULT '[]',
    entry_rule TEXT NOT NULL DEFAULT '',
    exit_rule TEXT NOT NULL DEFAULT '',
    cost_model_json TEXT NOT NULL DEFAULT '[]',
    success_metric TEXT NOT NULL DEFAULT '',
    reject_if TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'needs_data',
    scores_json TEXT NOT NULL DEFAULT '{}',
    notes TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_record_id) REFERENCES research_records(record_id),
    UNIQUE(source_record_id, experiment_type)
);

CREATE INDEX IF NOT EXISTS idx_experiment_specs_status
ON experiment_specs(status);

CREATE INDEX IF NOT EXISTS idx_experiment_specs_source_record
ON experiment_specs(source_record_id);

CREATE TABLE IF NOT EXISTS experiment_data_requirements (
    requirement_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    data_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'needed',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id) REFERENCES experiment_specs(experiment_id),
    UNIQUE(experiment_id, data_name)
);

CREATE INDEX IF NOT EXISTS idx_experiment_data_requirements_status
ON experiment_data_requirements(status);
"""


def init_db(db_path: Path | str) -> None:
    init_research_db(db_path)
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)

