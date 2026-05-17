from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from research_loop.config import ROOT
from research_loop.db import connect

from .binance_client import BinanceUSDMClient
from .data_vision_client import BinanceDataVisionClient
from .db import init_db
from .repository import DataRepository, dataset_path


DEFAULT_MARKET_DATA_DIR = ROOT / "data" / "market"


def plan_once(db_path: Path, limit: int = 25) -> dict[str, int]:
    init_db(db_path)
    with connect(db_path) as connection:
        repo = DataRepository(connection)
        return repo.create_jobs_from_requirements(limit=limit)


def collect_once(
    db_path: Path,
    data_dir: Path = DEFAULT_MARKET_DATA_DIR,
    limit: int = 5,
    client: BinanceUSDMClient | None = None,
    archive_client: BinanceDataVisionClient | None = None,
    retry_failed: bool = False,
) -> dict[str, int]:
    init_db(db_path)
    data_dir.mkdir(parents=True, exist_ok=True)
    client = client or BinanceUSDMClient()
    archive_client = archive_client or BinanceDataVisionClient()
    collected = 0
    failed = 0
    with connect(db_path) as connection:
        repo = DataRepository(connection)
        jobs = repo.pending_jobs(limit=limit, retry_failed=retry_failed)
        for job in jobs:
            repo.mark_job_running(job["job_id"])
            connection.commit()
            try:
                dataset = _collect_job(job, data_dir, client, archive_client)
                repo.mark_job_available(job, dataset)
                connection.commit()
                collected += 1
            except Exception as exc:  # pragma: no cover - exact network failures vary
                repo.mark_job_failed(job["job_id"], str(exc))
                connection.commit()
                failed += 1
    return {"jobs_seen": len(jobs), "jobs_collected": collected, "jobs_failed": failed}


def _collect_job(
    job: sqlite3.Row,
    data_dir: Path,
    client: BinanceUSDMClient,
    archive_client: BinanceDataVisionClient,
) -> dict[str, Any]:
    dataset_type = job["dataset_type"]
    symbol = job["symbol"]
    interval = job["interval"]
    path = dataset_path(data_dir, job["provider"], symbol, dataset_type, interval)
    source = "rest"
    if dataset_type == "ohlcv":
        rows = _collect_ohlcv(symbol, interval, client, archive_client)
        source = rows.pop(0)["source"] if rows and "source" in rows[0] else source
    elif dataset_type == "volume":
        rows = _collect_volume(symbol, interval, client, archive_client)
        source = rows.pop(0)["source"] if rows and "source" in rows[0] else source
    elif dataset_type == "funding_rates":
        rows = _collect_funding(symbol, client, archive_client)
        source = rows.pop(0)["source"] if rows and "source" in rows[0] else source
    elif dataset_type == "open_interest":
        rows = _collect_open_interest(symbol, interval, client, archive_client)
        source = rows.pop(0)["source"] if rows and "source" in rows[0] else source
    else:
        raise ValueError(f"unsupported dataset type: {dataset_type}")
    _write_csv(path, rows)
    return {
        "path": str(path),
        "row_count": len(rows),
        "start_at": rows[0]["timestamp"] if rows else "",
        "end_at": rows[-1]["timestamp"] if rows else "",
        "source": source,
    }


def _collect_ohlcv(
    symbol: str,
    interval: str,
    client: BinanceUSDMClient,
    archive_client: BinanceDataVisionClient,
) -> list[dict[str, str]]:
    try:
        rows = _normalize_klines(client.klines(symbol=symbol, interval=interval))
        return [{"source": "rest"}, *rows]
    except Exception:
        rows = _normalize_archive_klines(archive_client.klines(symbol=symbol, interval=interval))
        return [{"source": "data_vision"}, *rows]


def _collect_volume(
    symbol: str,
    interval: str,
    client: BinanceUSDMClient,
    archive_client: BinanceDataVisionClient,
) -> list[dict[str, str]]:
    try:
        rows = _normalize_volume(client.klines(symbol=symbol, interval=interval))
        return [{"source": "rest"}, *rows]
    except Exception:
        rows = _normalize_archive_volume(archive_client.klines(symbol=symbol, interval=interval))
        return [{"source": "data_vision"}, *rows]


def _collect_funding(
    symbol: str,
    client: BinanceUSDMClient,
    archive_client: BinanceDataVisionClient,
) -> list[dict[str, str]]:
    try:
        rows = _normalize_funding(client.funding_rates(symbol=symbol))
        return [{"source": "rest"}, *rows]
    except Exception:
        rows = _normalize_archive_funding(archive_client.funding_rates(symbol=symbol))
        return [{"source": "data_vision"}, *rows]


def _collect_open_interest(
    symbol: str,
    interval: str,
    client: BinanceUSDMClient,
    archive_client: BinanceDataVisionClient,
) -> list[dict[str, str]]:
    try:
        rows = _normalize_open_interest(client.open_interest_hist(symbol=symbol, period=interval))
        return [{"source": "rest"}, *rows]
    except Exception:
        rows = _normalize_archive_metrics(archive_client.metrics(symbol=symbol))
        return [{"source": "data_vision"}, *rows]


def _normalize_klines(items: list[Any]) -> list[dict[str, str]]:
    rows = []
    for item in items:
        rows.append(
            {
                "timestamp": _ms_to_iso(item[0]),
                "open": str(item[1]),
                "high": str(item[2]),
                "low": str(item[3]),
                "close": str(item[4]),
                "volume": str(item[5]),
                "close_time": _ms_to_iso(item[6]),
                "quote_volume": str(item[7]),
                "trade_count": str(item[8]),
            }
        )
    return rows


def _normalize_archive_klines(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for item in items:
        rows.append(
            {
                "timestamp": _ms_to_iso(item["open_time"]),
                "open": str(item["open"]),
                "high": str(item["high"]),
                "low": str(item["low"]),
                "close": str(item["close"]),
                "volume": str(item["volume"]),
                "close_time": _ms_to_iso(item["close_time"]),
                "quote_volume": str(item["quote_volume"]),
                "trade_count": str(item["count"]),
            }
        )
    return rows


def _normalize_volume(items: list[Any]) -> list[dict[str, str]]:
    rows = []
    for item in items:
        rows.append(
            {
                "timestamp": _ms_to_iso(item[0]),
                "volume": str(item[5]),
                "quote_volume": str(item[7]),
                "trade_count": str(item[8]),
            }
        )
    return rows


def _normalize_archive_volume(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for item in items:
        rows.append(
            {
                "timestamp": _ms_to_iso(item["open_time"]),
                "volume": str(item["volume"]),
                "quote_volume": str(item["quote_volume"]),
                "trade_count": str(item["count"]),
            }
        )
    return rows


def _normalize_funding(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for item in sorted(items, key=lambda value: int(value["fundingTime"])):
        rows.append(
            {
                "timestamp": _ms_to_iso(item["fundingTime"]),
                "funding_rate": str(item["fundingRate"]),
                "mark_price": str(item.get("markPrice", "")),
            }
        )
    return rows


def _normalize_archive_funding(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for item in sorted(items, key=lambda value: int(value["calc_time"])):
        rows.append(
            {
                "timestamp": _ms_to_iso(item["calc_time"]),
                "funding_rate": str(item["last_funding_rate"]),
                "funding_interval_hours": str(item.get("funding_interval_hours", "")),
            }
        )
    return rows


def _normalize_open_interest(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for item in sorted(items, key=lambda value: int(value["timestamp"])):
        rows.append(
            {
                "timestamp": _ms_to_iso(item["timestamp"]),
                "sum_open_interest": str(item.get("sumOpenInterest", "")),
                "sum_open_interest_value": str(item.get("sumOpenInterestValue", "")),
            }
        )
    return rows


def _normalize_archive_metrics(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for item in sorted(items, key=lambda value: value["create_time"]):
        rows.append(
            {
                "timestamp": _space_time_to_iso(item["create_time"]),
                "sum_open_interest": str(item.get("sum_open_interest", "")),
                "sum_open_interest_value": str(item.get("sum_open_interest_value", "")),
                "count_long_short_ratio": str(item.get("count_long_short_ratio", "")),
                "sum_taker_long_short_vol_ratio": str(item.get("sum_taker_long_short_vol_ratio", "")),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("collector returned no rows")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _ms_to_iso(value: int | str) -> str:
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).replace(microsecond=0).isoformat()


def _space_time_to_iso(value: str) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return parsed.replace(microsecond=0).isoformat()
