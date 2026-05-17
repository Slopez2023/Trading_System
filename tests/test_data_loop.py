from __future__ import annotations

from data_loop.collector import collect_once, plan_once
from data_loop.db import init_db
from data_loop.repository import DataRepository
from experiment_loop.models import ExperimentSpec
from experiment_loop.repository import ExperimentRepository
from research_loop.db import connect
from research_loop.models import RawItem, ResearchRecord, Source
from research_loop.repository import Repository


def test_data_loop_plans_btc_jobs_from_experiment_requirements(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    _insert_btc_experiment(db_path)

    result = plan_once(db_path, limit=10)

    with connect(db_path) as connection:
        jobs = DataRepository(connection).list_jobs(limit=10)

    assert result["data_jobs_created"] == 4
    assert {job["dataset_type"] for job in jobs} == {"ohlcv", "volume", "funding_rates", "open_interest"}
    assert {job["symbol"] for job in jobs} == {"BTCUSDT"}


def test_data_loop_collects_jobs_with_fake_binance_client(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    data_dir = tmp_path / "market"
    _insert_btc_experiment(db_path)
    plan_once(db_path, limit=10)

    result = collect_once(db_path, data_dir=data_dir, limit=10, client=FakeBinanceClient())

    with connect(db_path) as connection:
        repo = DataRepository(connection)
        jobs = repo.list_jobs(limit=10)
        datasets = repo.list_datasets(limit=10)
        requirement_statuses = connection.execute(
            """
            SELECT data_name, status
            FROM experiment_data_requirements
            ORDER BY data_name
            """
        ).fetchall()

    assert result == {"jobs_seen": 4, "jobs_collected": 4, "jobs_failed": 0}
    assert {job["status"] for job in jobs} == {"available"}
    assert {dataset["dataset_type"] for dataset in datasets} == {"ohlcv", "volume", "funding_rates", "open_interest"}
    assert {row["status"] for row in requirement_statuses} == {"available"}
    for dataset in datasets:
        assert dataset["row_count"] == 2
        assert data_dir in data_dir.parents or dataset["path"].startswith(str(data_dir))


class FakeBinanceClient:
    def klines(self, symbol: str, interval: str = "1h", limit: int = 500):
        assert symbol == "BTCUSDT"
        assert interval == "1h"
        return [
            [1700000000000, "100", "110", "95", "105", "123.4", 1700003599999, "13000", 10],
            [1700003600000, "105", "115", "101", "111", "150.0", 1700007199999, "16000", 12],
        ]

    def funding_rates(self, symbol: str, limit: int = 1000):
        assert symbol == "BTCUSDT"
        return [
            {"fundingTime": 1700000000000, "fundingRate": "0.0001", "markPrice": "100"},
            {"fundingTime": 1700028800000, "fundingRate": "-0.0002", "markPrice": "111"},
        ]

    def open_interest_hist(self, symbol: str, period: str = "1h", limit: int = 500):
        assert symbol == "BTCUSDT"
        assert period == "1h"
        return [
            {"timestamp": 1700000000000, "sumOpenInterest": "1000", "sumOpenInterestValue": "100000"},
            {"timestamp": 1700003600000, "sumOpenInterest": "1050", "sumOpenInterestValue": "116550"},
        ]


def _insert_btc_experiment(db_path) -> None:
    init_db(db_path)
    with connect(db_path) as connection:
        research_repo = Repository(connection)
        research_repo.upsert_source(Source(source_id="manual", source_type="manual", name="Manual", url="manual://input"))
        research_repo.insert_raw_items(
            [
                RawItem(
                    source_id="manual",
                    source_type="manual",
                    url="manual://btc",
                    title="BTC funding OI reversal",
                    text="Backtest BTC funding and open interest reversal.",
                )
            ]
        )
        raw = research_repo.claim_pending_raw_items(limit=1)[0]
        research_repo.insert_research_record(
            ResearchRecord(
                record_type="strategy_idea",
                title="BTC funding OI reversal",
                summary="Backtest BTC funding and open interest reversal.",
                markets=["crypto"],
                required_data=["funding_rates", "open_interest", "ohlcv", "volume"],
                status="needs_data",
            ),
            raw["raw_item_id"],
        )
        record = connection.execute("SELECT record_id FROM research_records").fetchone()
        ExperimentRepository(connection).insert_experiment_spec(
            ExperimentSpec(
                source_record_id=record["record_id"],
                thesis="BTC perpetual futures may reverse after extreme funding, rising open interest, and volume spikes.",
                experiment_type="signal_backtest",
                market="crypto perpetuals",
                asset="BTC",
                timeframes=["1h", "4h", "12h", "24h"],
                data_needed=["ohlcv", "volume", "funding_rates", "open_interest"],
                entry_rule="funding extreme and open interest rising",
                exit_rule="fixed holding windows",
                cost_model=["fees", "slippage"],
                success_metric="positive net expectancy after costs",
                reject_if="edge disappears after costs",
                status="needs_data",
                scores={"roi": 50},
            )
        )
        connection.commit()

