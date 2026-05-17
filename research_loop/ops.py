from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .db import connect, init_db


def backup_database(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"research_loop_{timestamp}.sqlite3"
    init_db(db_path)
    with sqlite3.connect(db_path) as source, sqlite3.connect(backup_path) as target:
        source.backup(target)
    return backup_path


def health_check(db_path: Path, log_path: Path) -> dict[str, Any]:
    init_db(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM sources WHERE status = 'active') AS active_sources,
                (SELECT COUNT(*) FROM sources WHERE last_error != '') AS sources_with_errors,
                (SELECT COUNT(*) FROM raw_items WHERE processing_status = 'pending') AS pending_raw_items,
                (SELECT COUNT(*) FROM raw_items WHERE processing_status = 'failed') AS failed_raw_items,
                (SELECT COUNT(*) FROM research_records WHERE fingerprint = '') AS blank_fingerprints,
                (
                    SELECT COUNT(*)
                    FROM research_records
                    WHERE json_extract(scores_json, '$.novelty') IS NULL
                       OR json_extract(scores_json, '$.data_availability') IS NULL
                       OR json_extract(scores_json, '$.source_quality') IS NULL
                ) AS missing_score_fields,
                (SELECT COUNT(*) FROM research_records WHERE status != 'archived') AS active_records
            """
        ).fetchone()
    last_log_event = _last_jsonl_event(log_path)
    status = "ok"
    if row["sources_with_errors"] or row["failed_raw_items"] or row["blank_fingerprints"] or row["missing_score_fields"]:
        status = "needs_attention"
    return {
        "status": status,
        "db_exists": Path(db_path).exists(),
        "active_sources": int(row["active_sources"]),
        "sources_with_errors": int(row["sources_with_errors"]),
        "pending_raw_items": int(row["pending_raw_items"]),
        "failed_raw_items": int(row["failed_raw_items"]),
        "blank_fingerprints": int(row["blank_fingerprints"]),
        "missing_score_fields": int(row["missing_score_fields"]),
        "active_records": int(row["active_records"]),
        "last_log_event": last_log_event,
    }


def ai_health(log_path: Path) -> dict[str, Any]:
    events = _jsonl_events(log_path)
    fallback_events = [event for event in events if event.get("event") == "ai_fallback"]
    run_events = [event for event in events if event.get("event") in {"run_once", "loop_cycle", "extract_once"}]
    last_fallback = fallback_events[-1] if fallback_events else {}
    return {
        "log_exists": log_path.exists(),
        "total_runtime_events": len(events),
        "extraction_run_events": len(run_events),
        "ai_fallbacks": len(fallback_events),
        "last_fallback_model": last_fallback.get("model", ""),
        "last_fallback_error": last_fallback.get("error", ""),
        "last_fallback_source_id": last_fallback.get("source_id", ""),
    }


def _last_jsonl_event(path: Path) -> dict[str, Any]:
    events = _jsonl_events(path)
    return events[-1] if events else {}


def _jsonl_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events
