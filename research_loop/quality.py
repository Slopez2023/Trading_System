from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .db import connect, init_db
from .dedupe import record_fingerprint
from .models import ResearchRecord
from .normalization import normalize_record
from .utils import from_json, to_json, utc_now


def repair_record_quality(db_path: Path) -> dict[str, int]:
    init_db(db_path)
    checked = 0
    fingerprints_updated = 0
    markets_updated = 0
    scores_updated = 0
    statuses_preserved = 0
    with connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM research_records ORDER BY created_at ASC").fetchall()
        for row in rows:
            checked += 1
            original_status = row["status"]
            original_markets = from_json(row["markets_json"], [])
            original_scores = from_json(row["scores_json"], {})
            record = _record_from_row(row)
            normalized = normalize_record(record)
            if original_status == "archived":
                normalized = replace(normalized, status="archived")
                statuses_preserved += 1
            fingerprint = record_fingerprint(normalized)
            if fingerprint != row["fingerprint"]:
                fingerprints_updated += 1
            if normalized.markets != original_markets:
                markets_updated += 1
            if normalized.scores != original_scores:
                scores_updated += 1
            connection.execute(
                """
                UPDATE research_records
                SET markets_json = ?,
                    tags_json = ?,
                    required_data_json = ?,
                    risks_json = ?,
                    scores_json = ?,
                    status = ?,
                    next_loop_targets_json = ?,
                    fingerprint = ?,
                    updated_at = ?
                WHERE record_id = ?
                """,
                (
                    to_json(normalized.markets),
                    to_json(normalized.tags),
                    to_json(normalized.required_data),
                    to_json(normalized.risks),
                    to_json(normalized.scores),
                    normalized.status,
                    to_json(normalized.next_loop_targets),
                    fingerprint,
                    utc_now(),
                    row["record_id"],
                ),
            )
        duplicate_clusters = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM (
                SELECT fingerprint
                FROM research_records
                WHERE fingerprint != '' AND status != 'archived'
                GROUP BY fingerprint
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()["count"]
        connection.commit()
    return {
        "records_checked": checked,
        "fingerprints_updated": fingerprints_updated,
        "markets_updated": markets_updated,
        "scores_updated": scores_updated,
        "archived_statuses_preserved": statuses_preserved,
        "active_duplicate_clusters": int(duplicate_clusters),
    }


def _record_from_row(row) -> ResearchRecord:
    return ResearchRecord(
        record_type=row["record_type"],
        title=row["title"],
        summary=row["summary"],
        details=row["details"],
        markets=from_json(row["markets_json"], []),
        assets=from_json(row["assets_json"], []),
        timeframes=from_json(row["timeframes_json"], []),
        tags=from_json(row["tags_json"], []),
        required_data=from_json(row["required_data_json"], []),
        risks=from_json(row["risks_json"], []),
        scores=from_json(row["scores_json"], {}),
        status=row["status"],
        next_loop_targets=from_json(row["next_loop_targets_json"], []),
    )
