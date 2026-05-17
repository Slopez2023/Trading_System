from __future__ import annotations

from research_loop.db import connect, init_db
from research_loop.event_log import append_event
from research_loop.models import RawItem, ResearchRecord, Source
from research_loop.ops import ai_health, backup_database, health_check
from research_loop.repository import Repository


def test_backup_database_creates_readable_copy(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    backup_dir = tmp_path / "backups"
    init_db(db_path)
    with connect(db_path) as connection:
        Repository(connection).upsert_source(Source(source_id="manual", source_type="manual", name="Manual", url="manual://input"))
        connection.commit()

    backup_path = backup_database(db_path, backup_dir)

    with connect(backup_path) as connection:
        assert Repository(connection).count_table("sources") == 1


def test_health_check_reports_quality_issues(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    log_path = tmp_path / "logs" / "research_loop.jsonl"
    init_db(db_path)
    with connect(db_path) as connection:
        repo = Repository(connection)
        repo.upsert_source(Source(source_id="manual", source_type="manual", name="Manual", url="manual://input"))
        repo.insert_raw_items(
            [
                RawItem(
                    source_id="manual",
                    source_type="manual",
                    url="manual://1",
                    title="Idea",
                    text="Backtest momentum.",
                )
            ]
        )
        raw = repo.claim_pending_raw_items(limit=1)[0]
        repo.insert_research_record(
            ResearchRecord(
                record_type="strategy_idea",
                title="Momentum",
                summary="Backtest momentum.",
                scores={"priority": 50},
            ),
            raw["raw_item_id"],
        )
        connection.execute("UPDATE research_records SET fingerprint = '', scores_json = '{\"priority\": 50}'")
        connection.commit()

    result = health_check(db_path, log_path)

    assert result["status"] == "needs_attention"
    assert result["blank_fingerprints"] == 1
    assert result["missing_score_fields"] == 1


def test_ai_health_summarizes_fallback_events(tmp_path) -> None:
    log_path = tmp_path / "logs" / "research_loop.jsonl"
    append_event(
        log_path,
        "ai_fallback",
        {
            "model": "deepseek/deepseek-v4-flash",
            "source_id": "reddit",
            "error": "model output was not valid JSON",
        },
    )

    result = ai_health(log_path)

    assert result["ai_fallbacks"] == 1
    assert result["last_fallback_model"] == "deepseek/deepseek-v4-flash"
