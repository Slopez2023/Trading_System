from __future__ import annotations

from research_loop.db import init_db, connect
from research_loop.models import RawItem, ResearchRecord, Source
from research_loop.repository import Repository


def test_repository_inserts_raw_item_and_record(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    init_db(db_path)
    with connect(db_path) as connection:
        repo = Repository(connection)
        repo.upsert_source(
            Source(
                source_id="test_source",
                source_type="rss",
                name="Test Source",
                url="https://example.com/feed.xml",
            )
        )
        inserted = repo.insert_raw_items(
            [
                RawItem(
                    source_id="test_source",
                    source_type="rss",
                    url="https://example.com/item",
                    title="Momentum test",
                    text="Backtest a momentum signal with volume.",
                )
            ]
        )
        assert inserted == 1
        raw = repo.claim_pending_raw_items(limit=1)[0]
        created = repo.insert_research_record(
            ResearchRecord(
                record_type="strategy_idea",
                title="Strategy idea: Momentum test",
                summary="Backtest a momentum signal with volume.",
                markets=["stocks"],
                tags=["momentum"],
                required_data=["price", "volume"],
                next_loop_targets=["backtest_loop"],
            ),
            raw["raw_item_id"],
        )
        repo.mark_raw_item_processed(raw["raw_item_id"], "extracted", 0.8)
        connection.commit()

    assert created is True
    with connect(db_path) as connection:
        repo = Repository(connection)
        assert repo.count_table("sources") == 1
        assert repo.count_table("raw_items") == 1
        assert repo.count_table("research_records") == 1
        assert repo.count_table("evidence_links") == 1


def test_repository_claims_pending_items_once(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    init_db(db_path)
    with connect(db_path) as connection:
        repo = Repository(connection)
        repo.upsert_source(Source(source_id="test_source", source_type="rss", name="Test", url="https://example.com"))
        repo.insert_raw_items(
            [
                RawItem(
                    source_id="test_source",
                    source_type="rss",
                    url="https://example.com/1",
                    title="Momentum idea",
                    text="Backtest momentum.",
                )
            ]
        )
        first_claim = repo.claim_pending_raw_items(limit=1)
        second_claim = repo.claim_pending_raw_items(limit=1)

    assert len(first_claim) == 1
    assert second_claim == []
