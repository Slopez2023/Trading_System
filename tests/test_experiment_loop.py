from __future__ import annotations

from experiment_loop.db import init_db
from experiment_loop.planner import plan_once, spec_from_research_record
from experiment_loop.repository import ExperimentRepository
from research_loop.db import connect
from research_loop.models import RawItem, ResearchRecord, Source
from research_loop.repository import Repository
from research_loop.utils import from_json


def test_planner_builds_btc_funding_experiment_spec(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    row = _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="BTC funding OI reversal strategy",
            summary="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike.",
            markets=["BTC perpetual futures", "crypto"],
            required_data=["funding rates", "open interest", "price", "volume"],
            risks=["slippage", "liquidation risk"],
            scores={"priority": 75, "confidence": 60, "data_availability": 80},
            status="needs_data",
        ),
    )

    spec = spec_from_research_record(row)

    assert spec is not None
    assert spec.experiment_type == "signal_backtest"
    assert spec.asset == "BTC"
    assert "funding_rates" in spec.data_needed
    assert "open_interest" in spec.data_needed
    assert spec.scores["roi"] > 40
    assert spec.status == "needs_data"


def test_planner_builds_exchange_listing_event_study(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    row = _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="Coinbase/Binance listing momentum and reversal strategy",
            summary="Test whether assets move around Coinbase and Binance listing announcements.",
            markets=["crypto"],
            required_data=["historical listing announcement timestamps", "price data", "volume data"],
            risks=["timestamp risk"],
            scores={"priority": 75, "confidence": 65, "data_availability": 70},
            status="needs_data",
        ),
    )

    spec = spec_from_research_record(row)

    assert spec is not None
    assert spec.experiment_type == "event_study"
    assert spec.asset == "listed crypto assets"
    assert "listing_announcement_timestamps" in spec.data_needed
    assert "liquidity_filters" in spec.data_needed


def test_plan_once_writes_specs_and_data_requirements_idempotently(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="BTC funding OI reversal strategy",
            summary="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike.",
            markets=["crypto"],
            required_data=["funding rates", "open interest", "price", "volume"],
            scores={"priority": 75, "confidence": 60, "data_availability": 80},
            status="needs_data",
        ),
    )

    init_db(db_path)
    with connect(db_path) as connection:
        first = plan_once(connection, limit=5)
    with connect(db_path) as connection:
        second = plan_once(connection, limit=5)
        repo = ExperimentRepository(connection)
        specs = repo.recent_experiment_specs(limit=10)
        requirements = connection.execute(
            "SELECT data_name FROM experiment_data_requirements ORDER BY data_name"
        ).fetchall()

    assert first["experiment_specs_written"] == 1
    assert second["experiment_specs_written"] == 1
    assert len(specs) == 1
    assert from_json(specs[0]["data_needed_json"], [])
    assert {row["data_name"] for row in requirements} >= {"funding_rates", "open_interest", "ohlcv"}


def test_planner_skips_generic_social_chatter(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    row = _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="Should I hold crypto after a drawdown?",
            summary="A user is frustrated with a 40% loss and asks whether to keep holding.",
            markets=["crypto"],
            required_data=["portfolio holdings", "cost basis", "market prices"],
            risks=["losses may continue"],
            scores={"priority": 45, "confidence": 40, "data_availability": 40},
            status="needs_data",
        ),
    )

    assert spec_from_research_record(row) is None


def _insert_record(db_path, record: ResearchRecord):
    init_db(db_path)
    with connect(db_path) as connection:
        repo = Repository(connection)
        repo.upsert_source(Source(source_id="manual", source_type="manual", name="Manual", url="manual://input"))
        repo.insert_raw_items(
            [
                RawItem(
                    source_id="manual",
                    source_type="manual",
                    url=f"manual://{record.title}",
                    title=record.title,
                    text=record.summary,
                )
            ]
        )
        raw = repo.claim_pending_raw_items(limit=1)[0]
        repo.insert_research_record(record, raw["raw_item_id"])
        connection.commit()
        return connection.execute("SELECT * FROM research_records WHERE title = ?", (record.title,)).fetchone()
