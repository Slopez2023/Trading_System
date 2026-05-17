from __future__ import annotations

import sqlite3
from pathlib import Path

from research_loop.utils import content_hash, from_json, to_json, utc_now


SUPPORTED_DATASETS = {
    "ohlcv": "ohlcv",
    "volume": "volume",
    "funding_rates": "funding_rates",
    "open_interest": "open_interest",
}


class DataRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create_jobs_from_requirements(self, limit: int = 25) -> dict[str, int]:
        rows = self.connection.execute(
            """
            SELECT r.requirement_id,
                   r.experiment_id,
                   r.data_name,
                   e.experiment_type,
                   e.asset,
                   e.market,
                   e.timeframes_json,
                   e.status AS experiment_status
            FROM experiment_data_requirements r
            JOIN experiment_specs e ON r.experiment_id = e.experiment_id
            WHERE r.status IN ('needed', 'pending')
            ORDER BY e.updated_at DESC, r.created_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        created = 0
        skipped = 0
        for row in rows:
            job = _job_from_requirement(row)
            if job is None:
                skipped += 1
                continue
            cursor = self._insert_job(**job)
            created += int(bool(cursor.rowcount))
        self.connection.commit()
        return {"requirements_seen": len(rows), "data_jobs_created": created, "requirements_skipped": skipped}

    def pending_jobs(self, limit: int = 10, retry_failed: bool = False) -> list[sqlite3.Row]:
        statuses = ("pending", "failed") if retry_failed else ("pending",)
        placeholders = ",".join("?" for _ in statuses)
        return self.connection.execute(
            f"""
            SELECT *
            FROM data_jobs
            WHERE status IN ({placeholders})
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (*statuses, limit),
        ).fetchall()

    def mark_job_running(self, job_id: str) -> None:
        self.connection.execute(
            """
            UPDATE data_jobs
            SET status = 'running', error = '', updated_at = ?
            WHERE job_id = ?
            """,
            (utc_now(), job_id),
        )

    def mark_job_failed(self, job_id: str, error: str) -> None:
        now = utc_now()
        self.connection.execute(
            """
            UPDATE data_jobs
            SET status = 'failed', error = ?, updated_at = ?
            WHERE job_id = ?
            """,
            (error[:1000], now, job_id),
        )

    def mark_job_available(self, job: sqlite3.Row, dataset: dict) -> str:
        now = utc_now()
        dataset_id = self.upsert_dataset(
            experiment_id=job["experiment_id"],
            dataset_type=job["dataset_type"],
            provider=job["provider"],
            symbol=job["symbol"],
            timeframe=job["interval"],
            path=dataset["path"],
            row_count=dataset["row_count"],
            start_at=dataset["start_at"],
            end_at=dataset["end_at"],
        )
        self.connection.execute(
            """
            UPDATE data_jobs
            SET status = 'available',
                dataset_id = ?,
                error = '',
                updated_at = ?
            WHERE job_id = ?
            """,
            (dataset_id, now, job["job_id"]),
        )
        self.connection.execute(
            """
            UPDATE experiment_data_requirements
            SET status = 'available', updated_at = ?
            WHERE requirement_id = ?
            """,
            (now, job["requirement_id"]),
        )
        return dataset_id

    def upsert_dataset(
        self,
        experiment_id: str,
        dataset_type: str,
        provider: str,
        symbol: str,
        timeframe: str,
        path: str,
        row_count: int,
        start_at: str,
        end_at: str,
    ) -> str:
        now = utc_now()
        dataset_hash = content_hash(experiment_id, dataset_type, provider, symbol, timeframe)
        dataset_id = f"ds_{dataset_hash[:16]}"
        self.connection.execute(
            """
            INSERT INTO market_datasets (
                dataset_id, experiment_id, dataset_type, provider, symbol,
                timeframe, path, row_count, start_at, end_at, status,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', ?, ?)
            ON CONFLICT(experiment_id, dataset_type, provider, symbol, timeframe) DO UPDATE SET
                path = excluded.path,
                row_count = excluded.row_count,
                start_at = excluded.start_at,
                end_at = excluded.end_at,
                status = 'available',
                updated_at = excluded.updated_at
            """,
            (dataset_id, experiment_id, dataset_type, provider, symbol, timeframe, path, row_count, start_at, end_at, now, now),
        )
        return dataset_id

    def list_jobs(self, limit: int = 25) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT *
            FROM data_jobs
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def list_datasets(self, limit: int = 25) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT *
            FROM market_datasets
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def count_table(self, table: str) -> int:
        allowed = {"data_jobs", "market_datasets"}
        if table not in allowed:
            raise ValueError(f"unsupported table: {table}")
        return int(self.connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])

    def _insert_job(
        self,
        experiment_id: str,
        requirement_id: str,
        data_name: str,
        dataset_type: str,
        provider: str,
        symbol: str,
        interval: str,
    ) -> sqlite3.Cursor:
        now = utc_now()
        job_hash = content_hash(experiment_id, data_name, provider, symbol, interval)
        return self.connection.execute(
            """
            INSERT OR IGNORE INTO data_jobs (
                job_id, experiment_id, requirement_id, data_name, dataset_type,
                provider, symbol, interval, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (f"job_{job_hash[:16]}", experiment_id, requirement_id, data_name, dataset_type, provider, symbol, interval, now, now),
        )


def _job_from_requirement(row: sqlite3.Row) -> dict | None:
    data_name = str(row["data_name"]).strip()
    dataset_type = SUPPORTED_DATASETS.get(data_name)
    if dataset_type is None:
        return None
    symbol = _symbol_for_spec(row["asset"], row["market"])
    if symbol != "BTCUSDT":
        return None
    return {
        "experiment_id": row["experiment_id"],
        "requirement_id": row["requirement_id"],
        "data_name": data_name,
        "dataset_type": dataset_type,
        "provider": "binance_usdm",
        "symbol": symbol,
        "interval": _interval_for_dataset(dataset_type, from_json(row["timeframes_json"], [])),
    }


def _symbol_for_spec(asset: str, market: str) -> str:
    text = f"{asset} {market}".upper()
    if "BTC" in text:
        return "BTCUSDT"
    return ""


def _interval_for_dataset(dataset_type: str, timeframes: list[str]) -> str:
    if dataset_type in {"ohlcv", "volume", "open_interest"}:
        return "1h" if "1h" in timeframes or not timeframes else str(timeframes[0])
    return "8h"


def dataset_path(root: Path, provider: str, symbol: str, dataset_type: str, interval: str) -> Path:
    filename = f"{symbol.lower()}_{provider}_{dataset_type}_{interval}.csv"
    return root / filename
