from __future__ import annotations

import json

from research_loop.db import connect, init_db
from research_loop.models import RawItem, ResearchRecord, Source
from research_loop.record_export import export_records
from research_loop.repository import Repository


def test_export_records_includes_evidence_links(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    output_path = tmp_path / "records.json"
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
                    title="BTC funding",
                    text="Backtest BTC funding reversal.",
                )
            ]
        )
        raw = repo.claim_pending_raw_items(limit=1)[0]
        repo.insert_research_record(
            ResearchRecord(
                record_type="strategy_idea",
                title="BTC funding reversal",
                summary="Backtest BTC funding reversal.",
                markets=["crypto"],
                required_data=["funding rates"],
                status="needs_data",
                next_loop_targets=["validation_loop"],
            ),
            raw["raw_item_id"],
        )
        connection.commit()

    export_records(db_path, output_path, limit=10)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["record_count"] == 1
    assert payload["records"][0]["title"] == "BTC funding reversal"
    assert payload["records"][0]["evidence"][0]["source_id"] == "manual"
