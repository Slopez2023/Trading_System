from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .db import connect, init_db
from .utils import from_json


def export_records(db_path: Path, output_path: Path, limit: int = 100, status: str | None = None) -> Path:
    init_db(db_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with connect(db_path) as connection:
        rows = _record_rows(connection, limit=limit, status=status)
        for row in rows:
            records.append(_record_payload(connection, row))
    payload = {
        "version": 1,
        "record_count": len(records),
        "records": records,
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def _record_rows(connection, limit: int, status: str | None) -> list[Any]:
    if status:
        return connection.execute(
            """
            SELECT *
            FROM research_records
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (status, limit),
        ).fetchall()
    return connection.execute(
        """
        SELECT *
        FROM research_records
        WHERE status != 'archived'
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def _record_payload(connection, row) -> dict[str, Any]:
    evidence_rows = connection.execute(
        """
        SELECT evidence_links.relationship,
               evidence_links.summary,
               evidence_links.confidence,
               raw_items.raw_item_id,
               raw_items.source_id,
               raw_items.source_type,
               raw_items.url,
               raw_items.title,
               raw_items.published_at,
               raw_items.collected_at
        FROM evidence_links
        JOIN raw_items ON evidence_links.raw_item_id = raw_items.raw_item_id
        WHERE evidence_links.record_id = ?
        ORDER BY evidence_links.created_at ASC
        """,
        (row["record_id"],),
    ).fetchall()
    return {
        "record_id": row["record_id"],
        "record_type": row["record_type"],
        "title": row["title"],
        "summary": row["summary"],
        "details": row["details"],
        "markets": from_json(row["markets_json"], []),
        "assets": from_json(row["assets_json"], []),
        "timeframes": from_json(row["timeframes_json"], []),
        "tags": from_json(row["tags_json"], []),
        "required_data": from_json(row["required_data_json"], []),
        "risks": from_json(row["risks_json"], []),
        "scores": from_json(row["scores_json"], {}),
        "status": row["status"],
        "next_loop_targets": from_json(row["next_loop_targets_json"], []),
        "fingerprint": row["fingerprint"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "evidence": [
            {
                "raw_item_id": evidence["raw_item_id"],
                "source_id": evidence["source_id"],
                "source_type": evidence["source_type"],
                "url": evidence["url"],
                "title": evidence["title"],
                "published_at": evidence["published_at"],
                "collected_at": evidence["collected_at"],
                "relationship": evidence["relationship"],
                "summary": evidence["summary"],
                "confidence": evidence["confidence"],
            }
            for evidence in evidence_rows
        ],
    }
