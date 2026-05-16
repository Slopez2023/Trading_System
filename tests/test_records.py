from __future__ import annotations

from research_loop.db import connect, init_db
from research_loop.models import RawItem, ResearchRecord, Source
from research_loop.repository import Repository


def test_archive_records_hides_from_recent_records(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
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
                    title="Test idea",
                    text="Backtest a momentum idea.",
                )
            ]
        )
        raw = repo.claim_pending_raw_items(limit=1)[0]
        repo.insert_research_record(
            ResearchRecord(
                record_type="strategy_idea",
                title="Strategy idea: Test",
                summary="Test summary",
            ),
            raw["raw_item_id"],
        )
        assert len(repo.recent_research_records(limit=10)) == 1
        archived = repo.archive_research_records()
        connection.commit()

    assert archived == 1
    with connect(db_path) as connection:
        repo = Repository(connection)
        assert repo.recent_research_records(limit=10) == []


def test_insert_research_record_revives_archived_duplicate(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
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
                    title="Test idea",
                    text="Backtest a momentum idea.",
                )
            ]
        )
        raw = repo.claim_pending_raw_items(limit=1)[0]
        record = ResearchRecord(
            record_type="strategy_idea",
            title="Strategy idea: Test",
            summary="Test summary",
            status="needs_review",
        )
        repo.insert_research_record(record, raw["raw_item_id"])
        repo.archive_research_records()
        repo.insert_research_record(record, raw["raw_item_id"])
        connection.commit()

    with connect(db_path) as connection:
        row = connection.execute("SELECT status FROM research_records").fetchone()
        assert row["status"] == "needs_review"
