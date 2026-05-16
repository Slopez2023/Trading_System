from __future__ import annotations

import sqlite3
import uuid
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

    def mark_source_checked(self, source_id: str) -> None:
        self.connection.execute(
            "UPDATE sources SET last_checked_at = ?, updated_at = ? WHERE source_id = ?",
            (utc_now(), utc_now(), source_id),
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

    def list_pending_raw_items(self, limit: int = 50) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT raw_items.*, sources.markets_json AS source_markets_json,
                   sources.topics_json AS source_topics_json
            FROM raw_items
            JOIN sources ON raw_items.source_id = sources.source_id
            WHERE processing_status = 'pending'
            ORDER BY collected_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def mark_raw_item_processed(self, raw_item_id: str, status: str, relevance_score: float | None) -> None:
        self.connection.execute(
            """
            UPDATE raw_items
            SET processing_status = ?, relevance_score = ?
            WHERE raw_item_id = ?
            """,
            (status, relevance_score, raw_item_id),
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
            INSERT OR IGNORE INTO research_records (
                record_id, record_type, title, summary, details,
                markets_json, assets_json, timeframes_json, tags_json,
                required_data_json, risks_json, scores_json, status,
                next_loop_targets_json, content_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ORDER BY created_at DESC
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
