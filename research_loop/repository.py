from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Iterable

from .models import RawItem, ResearchRecord, Source
from .utils import content_hash, from_json, stable_json, to_json, utc_now


class Repository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def upsert_source(self, source: Source) -> None:
        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO sources (
                source_id, source_type, name, url, markets_json, topics_json,
                status, check_frequency_minutes, quality_score, noise_score,
                metadata_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                source_type = excluded.source_type,
                name = excluded.name,
                url = excluded.url,
                markets_json = excluded.markets_json,
                topics_json = excluded.topics_json,
                status = excluded.status,
                check_frequency_minutes = excluded.check_frequency_minutes,
                quality_score = excluded.quality_score,
                noise_score = excluded.noise_score,
                metadata_json = excluded.metadata_json,
                updated_at = excluded.updated_at
            """,
            (
                source.source_id,
                source.source_type,
                source.name,
                source.url,
                to_json(source.markets),
                to_json(source.topics),
                source.status,
                source.check_frequency_minutes,
                source.quality_score,
                source.noise_score,
                to_json(source.metadata),
                now,
                now,
            ),
        )
        self.connection.execute(
            """
            INSERT INTO source_performance (source_id, updated_at)
            VALUES (?, ?)
            ON CONFLICT(source_id) DO NOTHING
            """,
            (source.source_id, now),
        )

    def list_active_sources(self) -> list[Source]:
        rows = self.connection.execute(
            """
            SELECT * FROM sources
            WHERE status = 'active'
            ORDER BY source_type, name
            """
        ).fetchall()
        return [self._source_from_row(row) for row in rows]

    def list_sources(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT source_id, source_type, name, status, check_frequency_minutes,
                   last_checked_at, last_failed_at, failure_count, last_error
            FROM sources
            ORDER BY source_type, name
            """
        ).fetchall()

    def list_due_sources(self) -> list[Source]:
        now = datetime.now(timezone.utc)
        due = []
        for source in self.list_active_sources():
            row = self.connection.execute(
                "SELECT last_checked_at FROM sources WHERE source_id = ?",
                (source.source_id,),
            ).fetchone()
            if _is_due(row["last_checked_at"] if row else None, source.check_frequency_minutes, now):
                due.append(source)
        return due

    def set_source_status(self, source_id: str, status: str) -> bool:
        cursor = self.connection.execute(
            "UPDATE sources SET status = ?, updated_at = ? WHERE source_id = ?",
            (status, utc_now(), source_id),
        )
        return bool(cursor.rowcount)

    def mark_source_checked(self, source_id: str) -> None:
        self.connection.execute(
            """
            UPDATE sources
            SET last_checked_at = ?, updated_at = ?, last_error = ''
            WHERE source_id = ?
            """,
            (utc_now(), utc_now(), source_id),
        )

    def mark_source_failed(self, source_id: str, error: str) -> None:
        self.connection.execute(
            """
            UPDATE sources
            SET last_failed_at = ?,
                last_error = ?,
                failure_count = failure_count + 1,
                updated_at = ?
            WHERE source_id = ?
            """,
            (utc_now(), error[:1000], utc_now(), source_id),
        )

    def insert_raw_items(self, raw_items: Iterable[RawItem]) -> int:
        inserted = 0
        now = utc_now()
        for raw in raw_items:
            item_hash = content_hash(raw.source_id, raw.url, raw.title, raw.text)
            raw_item_id = f"raw_{item_hash[:16]}"
            cursor = self.connection.execute(
                """
                INSERT OR IGNORE INTO raw_items (
                    raw_item_id, source_id, source_type, url, author,
                    published_at, collected_at, title, text, metadata_json,
                    content_hash, processing_status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    raw_item_id,
                    raw.source_id,
                    raw.source_type,
                    raw.url,
                    raw.author,
                    raw.published_at,
                    now,
                    raw.title.strip(),
                    raw.text.strip(),
                    to_json(raw.metadata),
                    item_hash,
                    now,
                ),
            )
            if cursor.rowcount:
                inserted += 1
                self.connection.execute(
                    """
                    UPDATE source_performance
                    SET total_items_seen = total_items_seen + 1, updated_at = ?
                    WHERE source_id = ?
                    """,
                    (now, raw.source_id),
                )
        return inserted

    def claim_pending_raw_items(self, limit: int = 50) -> list[sqlite3.Row]:
        now = utc_now()
        rows = self.connection.execute(
            """
            SELECT raw_item_id
            FROM raw_items
            WHERE processing_status = 'pending'
            ORDER BY collected_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        ids = [row["raw_item_id"] for row in rows]
        for raw_item_id in ids:
            self.connection.execute(
                """
                UPDATE raw_items
                SET processing_status = 'processing',
                    processing_started_at = ?,
                    processing_error = ''
                WHERE raw_item_id = ? AND processing_status = 'pending'
                """,
                (now, raw_item_id),
            )
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        return self.connection.execute(
            f"""
            SELECT raw_items.*, sources.markets_json AS source_markets_json,
                   sources.topics_json AS source_topics_json
            FROM raw_items
            JOIN sources ON raw_items.source_id = sources.source_id
            WHERE raw_items.raw_item_id IN ({placeholders})
            ORDER BY collected_at ASC
            """,
            ids,
        ).fetchall()

    def list_raw_items(self, status: str | None = None, limit: int = 25) -> list[sqlite3.Row]:
        if status:
            return self.connection.execute(
                """
                SELECT raw_item_id, source_id, processing_status, relevance_score,
                       collected_at, processed_at, title, processing_error
                FROM raw_items
                WHERE processing_status = ?
                ORDER BY collected_at DESC
                LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        return self.connection.execute(
            """
            SELECT raw_item_id, source_id, processing_status, relevance_score,
                   collected_at, processed_at, title, processing_error
            FROM raw_items
            ORDER BY collected_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def mark_raw_item_processed(self, raw_item_id: str, status: str, relevance_score: float | None) -> None:
        self.connection.execute(
            """
            UPDATE raw_items
            SET processing_status = ?,
                relevance_score = ?,
                processed_at = ?,
                processing_error = ''
            WHERE raw_item_id = ?
            """,
            (status, relevance_score, utc_now(), raw_item_id),
        )

    def mark_raw_item_failed(self, raw_item_id: str, error: str) -> None:
        self.connection.execute(
            """
            UPDATE raw_items
            SET processing_status = 'failed',
                processed_at = ?,
                processing_error = ?
            WHERE raw_item_id = ?
            """,
            (utc_now(), error[:1000], raw_item_id),
        )

    def insert_research_record(self, record: ResearchRecord, raw_item_id: str) -> bool:
        now = utc_now()
        record_hash = content_hash(
            record.record_type,
            record.title,
            record.summary,
            stable_json(record.markets),
            stable_json(record.assets),
            stable_json(record.tags),
        )
        record_id = f"rec_{record_hash[:16]}"
        cursor = self.connection.execute(
            """
            INSERT INTO research_records (
                record_id, record_type, title, summary, details,
                markets_json, assets_json, timeframes_json, tags_json,
                required_data_json, risks_json, scores_json, status,
                next_loop_targets_json, content_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(content_hash) DO UPDATE SET
                summary = excluded.summary,
                details = excluded.details,
                markets_json = excluded.markets_json,
                assets_json = excluded.assets_json,
                timeframes_json = excluded.timeframes_json,
                tags_json = excluded.tags_json,
                required_data_json = excluded.required_data_json,
                risks_json = excluded.risks_json,
                scores_json = excluded.scores_json,
                status = excluded.status,
                next_loop_targets_json = excluded.next_loop_targets_json,
                updated_at = excluded.updated_at
            """,
            (
                record_id,
                record.record_type,
                record.title,
                record.summary,
                record.details,
                to_json(record.markets),
                to_json(record.assets),
                to_json(record.timeframes),
                to_json(record.tags),
                to_json(record.required_data),
                to_json(record.risks),
                to_json(record.scores),
                record.status,
                to_json(record.next_loop_targets),
                record_hash,
                now,
                now,
            ),
        )
        self.connection.execute(
            """
            INSERT OR IGNORE INTO evidence_links (
                link_id, record_id, raw_item_id, relationship, summary, confidence, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"evi_{uuid.uuid4().hex[:16]}",
                record_id,
                raw_item_id,
                record.evidence_relationship,
                record.evidence_summary,
                record.scores.get("confidence", 50) / 100,
                now,
            ),
        )
        if cursor.rowcount:
            raw = self.connection.execute(
                "SELECT source_id FROM raw_items WHERE raw_item_id = ?",
                (raw_item_id,),
            ).fetchone()
            if raw:
                self.connection.execute(
                    """
                    UPDATE source_performance
                    SET items_used = items_used + 1,
                        records_created = records_created + 1,
                        updated_at = ?
                    WHERE source_id = ?
                    """,
                    (now, raw["source_id"]),
                )
            return True
        return False

    def recent_research_records(self, limit: int = 25) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT *
            FROM research_records
            WHERE status != 'archived'
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def archive_research_records(self, before: str | None = None) -> int:
        if before:
            cursor = self.connection.execute(
                """
                UPDATE research_records
                SET status = 'archived', updated_at = ?
                WHERE status != 'archived' AND created_at < ?
                """,
                (utc_now(), before),
            )
        else:
            cursor = self.connection.execute(
                """
                UPDATE research_records
                SET status = 'archived', updated_at = ?
                WHERE status != 'archived'
                """,
                (utc_now(),),
            )
        return int(cursor.rowcount)

    def reset_raw_items_for_reprocess(self, status: str = "extracted", limit: int = 50) -> int:
        rows = self.connection.execute(
            """
            SELECT raw_item_id
            FROM raw_items
            WHERE processing_status = ?
            ORDER BY collected_at DESC
            LIMIT ?
            """,
            (status, limit),
        ).fetchall()
        ids = [row["raw_item_id"] for row in rows]
        for raw_item_id in ids:
            self.connection.execute(
                """
                UPDATE raw_items
                SET processing_status = 'pending',
                    processing_started_at = NULL,
                    processed_at = NULL,
                    processing_error = ''
                WHERE raw_item_id = ?
                """,
                (raw_item_id,),
            )
        return len(ids)

    def source_status_counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM sources
            GROUP BY status
            """
        ).fetchall()
        return {row["status"]: int(row["count"]) for row in rows}

    def raw_status_counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            """
            SELECT processing_status, COUNT(*) AS count
            FROM raw_items
            GROUP BY processing_status
            """
        ).fetchall()
        return {row["processing_status"]: int(row["count"]) for row in rows}

    def record_type_counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            """
            SELECT record_type, COUNT(*) AS count
            FROM research_records
            WHERE status != 'archived'
            GROUP BY record_type
            ORDER BY count DESC, record_type ASC
            """
        ).fetchall()
        return {row["record_type"]: int(row["count"]) for row in rows}

    def latest_source_errors(self, limit: int = 5) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT source_id, last_failed_at, failure_count, last_error
            FROM sources
            WHERE last_error != ''
            ORDER BY last_failed_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def count_table(self, table: str) -> int:
        allowed = {"sources", "raw_items", "research_records", "evidence_links"}
        if table not in allowed:
            raise ValueError(f"unsupported table: {table}")
        return int(self.connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])

    @staticmethod
    def _source_from_row(row: sqlite3.Row) -> Source:
        return Source(
            source_id=row["source_id"],
            source_type=row["source_type"],
            name=row["name"],
            url=row["url"],
            markets=from_json(row["markets_json"], []),
            topics=from_json(row["topics_json"], []),
            status=row["status"],
            check_frequency_minutes=row["check_frequency_minutes"],
            quality_score=row["quality_score"],
            noise_score=row["noise_score"],
            metadata=from_json(row["metadata_json"], {}),
        )


def _is_due(last_checked_at: str | None, frequency_minutes: int, now: datetime) -> bool:
    if frequency_minutes <= 0:
        return True
    if not last_checked_at:
        return True
    try:
        checked_at = datetime.fromisoformat(last_checked_at)
    except ValueError:
        return True
    if checked_at.tzinfo is None:
        checked_at = checked_at.replace(tzinfo=timezone.utc)
    elapsed_seconds = (now - checked_at).total_seconds()
    return elapsed_seconds >= frequency_minutes * 60
