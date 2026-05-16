from __future__ import annotations

from research_loop.config import Settings
from research_loop.db import connect, init_db
from research_loop.models import RawItem, ResearchRecord, Source
from research_loop.monitor import render_monitor
from research_loop.repository import Repository


def test_render_monitor_includes_core_sections(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("TERM", raising=False)
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
                    title="BTC funding idea",
                    text="Backtest BTC funding reversals.",
                )
            ]
        )
        raw = repo.claim_pending_raw_items(limit=1)[0]
        repo.insert_research_record(
            ResearchRecord(
                record_type="strategy_idea",
                title="Strategy idea: BTC funding idea",
                summary="Backtest BTC funding reversals.",
                markets=["crypto"],
                scores={"priority": 80, "confidence": 60},
            ),
            raw["raw_item_id"],
        )
        repo.mark_raw_item_processed(raw["raw_item_id"], "extracted", 0.8)
        connection.commit()

    output = render_monitor(Settings(db_path=db_path), limit=5)

    assert "Trading Research Loop Monitor" in output
    assert "Sources" in output
    assert "Raw Items" in output
    assert "Research Records" in output
    assert "Strategy idea: BTC funding idea" in output
