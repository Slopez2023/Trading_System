from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    markets_json TEXT NOT NULL DEFAULT '[]',
    topics_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    check_frequency_minutes INTEGER NOT NULL DEFAULT 60,
    quality_score REAL NOT NULL DEFAULT 0.5,
    noise_score REAL NOT NULL DEFAULT 0.5,
    last_checked_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_items (
    raw_item_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    url TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    published_at TEXT NOT NULL DEFAULT '',
    collected_at TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    content_hash TEXT NOT NULL UNIQUE,
    processing_status TEXT NOT NULL DEFAULT 'pending',
    relevance_score REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_items_processing_status
ON raw_items(processing_status);

CREATE INDEX IF NOT EXISTS idx_raw_items_source_id
ON raw_items(source_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_items_source_url
ON raw_items(source_id, url)
WHERE url != '';

CREATE TABLE IF NOT EXISTS research_records (
    record_id TEXT PRIMARY KEY,
    record_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    markets_json TEXT NOT NULL DEFAULT '[]',
    assets_json TEXT NOT NULL DEFAULT '[]',
    timeframes_json TEXT NOT NULL DEFAULT '[]',
    tags_json TEXT NOT NULL DEFAULT '[]',
    required_data_json TEXT NOT NULL DEFAULT '[]',
    risks_json TEXT NOT NULL DEFAULT '[]',
    scores_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'captured',
    next_loop_targets_json TEXT NOT NULL DEFAULT '[]',
    content_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_research_records_type
ON research_records(record_type);

CREATE INDEX IF NOT EXISTS idx_research_records_status
ON research_records(status);

CREATE TABLE IF NOT EXISTS evidence_links (
    link_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL,
    raw_item_id TEXT NOT NULL,
    relationship TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES research_records(record_id),
    FOREIGN KEY (raw_item_id) REFERENCES raw_items(raw_item_id),
    UNIQUE(record_id, raw_item_id, relationship)
);

CREATE TABLE IF NOT EXISTS source_performance (
    source_id TEXT PRIMARY KEY,
    total_items_seen INTEGER NOT NULL DEFAULT 0,
    items_used INTEGER NOT NULL DEFAULT 0,
    records_created INTEGER NOT NULL DEFAULT 0,
    records_promoted INTEGER NOT NULL DEFAULT 0,
    records_rejected INTEGER NOT NULL DEFAULT 0,
    avg_quality_score REAL NOT NULL DEFAULT 0.5,
    last_high_value_item_at TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS processing_jobs (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL,
    finished_at TEXT
);
"""


def connect(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path | str) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)
