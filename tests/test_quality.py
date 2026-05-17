from __future__ import annotations

from research_loop.db import connect, init_db
from research_loop.models import RawItem, ResearchRecord, Source
from research_loop.quality import repair_record_quality
from research_loop.repository import Repository
from research_loop.utils import from_json


def test_repair_record_quality_backfills_fingerprint_scores_and_markets(tmp_path) -> None:
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
                    title="Bridge fees",
                    text="Hidden bridge fees can erase crypto arbitrage edge.",
                )
            ]
        )
        raw = repo.claim_pending_raw_items(limit=1)[0]
        repo.insert_research_record(
            ResearchRecord(
                record_type="risk_warning",
                title="Bridge hidden fee risk",
                summary="Hidden bridge fees can erase crypto arbitrage edge.",
                markets=["crypto", "forex", "futures", "options", "stocks"],
                scores={"priority": 62},
                status="risk_only",
            ),
            raw["raw_item_id"],
        )
        connection.execute("UPDATE research_records SET fingerprint = '', status = 'archived'")
        connection.commit()

    result = repair_record_quality(db_path)

    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM research_records").fetchone()

    assert result["fingerprints_updated"] == 1
    assert row["fingerprint"]
    assert row["status"] == "archived"
    assert from_json(row["markets_json"], []) == ["crypto"]
    assert "source_quality" in from_json(row["scores_json"], {})
