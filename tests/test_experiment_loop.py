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


def test_plan_once_overfetches_past_invalid_high_priority_records(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    for index in range(5):
        _insert_record(
            db_path,
            ResearchRecord(
                record_type="strategy_idea",
                title=f"Unsupported high priority idea {index}",
                summary="Watch vague macro chatter without a testable setup.",
                scores={"priority": 95 - index, "confidence": 40, "data_availability": 30},
                status="needs_data",
            ),
        )
    _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="Lower priority BTC funding OI reversal strategy",
            summary="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike.",
            markets=["crypto"],
            required_data=["funding rates", "open interest", "price"],
            scores={"priority": 50, "confidence": 60, "data_availability": 80},
            status="needs_data",
        ),
    )

    init_db(db_path)
    with connect(db_path) as connection:
        result = plan_once(connection, limit=1)
        repo = ExperimentRepository(connection)
        specs = repo.recent_experiment_specs(limit=10)

    assert result["experiment_specs_written"] == 1
    assert len(specs) == 1
    assert specs[0]["experiment_type"] == "signal_backtest"


def test_planner_does_not_treat_generic_announcements_as_listings(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    row = _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="Fed announcement BTC volatility study",
            summary="Test whether a Fed announcement affects BTC volatility after the press conference.",
            markets=["crypto"],
            required_data=["price data", "volume data"],
            scores={"priority": 80, "confidence": 60, "data_availability": 75},
            status="needs_data",
        ),
    )

    assert spec_from_research_record(row) is None


def test_plan_once_uses_explicit_experiment_loop_routing(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="BTC funding OI routed elsewhere",
            summary="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike.",
            markets=["crypto"],
            required_data=["funding rates", "open interest", "price"],
            scores={"priority": 80, "confidence": 60, "data_availability": 80},
            status="needs_data",
            next_loop_targets=["review_loop"],
        ),
    )
    _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="BTC funding OI routed to experiment loop",
            summary="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike.",
            markets=["crypto"],
            required_data=["funding rates", "open interest", "price"],
            scores={"priority": 70, "confidence": 60, "data_availability": 80},
            status="needs_data",
            next_loop_targets=["experiment_loop"],
        ),
    )

    init_db(db_path)
    with connect(db_path) as connection:
        result = plan_once(connection, limit=5)
        specs = ExperimentRepository(connection).recent_experiment_specs(limit=10)

    assert result["experiment_specs_written"] == 1
    assert len(specs) == 1
    assert specs[0]["source_record_id"]


def test_plan_once_skips_records_routed_only_to_other_loops(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="BTC funding OI routed only to review",
            summary="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike.",
            markets=["crypto"],
            required_data=["funding rates", "open interest", "price"],
            scores={"priority": 80, "confidence": 60, "data_availability": 80},
            status="needs_data",
            next_loop_targets=["review_loop"],
        ),
    )

    init_db(db_path)
    with connect(db_path) as connection:
        result = plan_once(connection, limit=5)
        specs = ExperimentRepository(connection).recent_experiment_specs(limit=10)

    assert result["experiment_specs_written"] == 0
    assert specs == []


def test_rerun_preserves_available_data_requirement_status(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="BTC funding OI status preservation",
            summary="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike.",
            markets=["crypto"],
            required_data=["funding rates", "open interest", "price"],
            scores={"priority": 75, "confidence": 60, "data_availability": 80},
            status="needs_data",
        ),
    )

    init_db(db_path)
    with connect(db_path) as connection:
        plan_once(connection, limit=5)
        connection.execute(
            "UPDATE experiment_data_requirements SET status = 'available' WHERE data_name = 'ohlcv'"
        )
        plan_once(connection, limit=5)
        row = connection.execute(
            "SELECT status FROM experiment_data_requirements WHERE data_name = 'ohlcv'"
        ).fetchone()

    assert row["status"] == "available"


def test_planner_does_not_treat_delisting_as_listing_event(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    row = _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="Exchange delisting risk study",
            summary="Test whether exchange delisting risk predicts downside volatility.",
            markets=["crypto"],
            required_data=["price data", "volume data"],
            scores={"priority": 80, "confidence": 60, "data_availability": 75},
            status="needs_data",
        ),
    )

    assert spec_from_research_record(row) is None


def test_sync_data_requirements_marks_removed_requirements_obsolete(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    row = _insert_record(
        db_path,
        ResearchRecord(
            record_type="strategy_idea",
            title="BTC funding OI reversal changing data needs",
            summary="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike.",
            markets=["crypto"],
            required_data=["funding rates", "open interest", "price", "volume"],
            scores={"priority": 75, "confidence": 60, "data_availability": 80},
            status="needs_data",
        ),
    )
    init_db(db_path)
    with connect(db_path) as connection:
        spec = spec_from_research_record(row)
        assert spec is not None
        repo = ExperimentRepository(connection)
        repo.insert_experiment_spec(spec)
        narrowed = spec.__class__(
            source_record_id=spec.source_record_id,
            thesis=spec.thesis,
            experiment_type=spec.experiment_type,
            market=spec.market,
            asset=spec.asset,
            timeframes=spec.timeframes,
            data_needed=["ohlcv"],
            entry_rule=spec.entry_rule,
            exit_rule=spec.exit_rule,
            cost_model=spec.cost_model,
            success_metric=spec.success_metric,
            reject_if=spec.reject_if,
            status=spec.status,
            scores=spec.scores,
            notes=spec.notes,
        )
        repo.insert_experiment_spec(narrowed)
        rows = connection.execute(
            "SELECT data_name, status FROM experiment_data_requirements ORDER BY data_name"
        ).fetchall()

    statuses = {row["data_name"]: row["status"] for row in rows}
    assert statuses["ohlcv"] == "needed"
    assert statuses["funding_rates"] == "obsolete"
    assert statuses["open_interest"] == "obsolete"


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
