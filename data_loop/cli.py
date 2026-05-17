from __future__ import annotations

import argparse
from pathlib import Path

from research_loop.config import DEFAULT_DB_PATH
from research_loop.db import connect

from .collector import DEFAULT_MARKET_DATA_DIR, collect_once, plan_once
from .db import init_db
from .repository import DataRepository


def main() -> None:
    parser = argparse.ArgumentParser(prog="data-loop")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_MARKET_DATA_DIR)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db")
    plan_parser = subparsers.add_parser("plan-once")
    plan_parser.add_argument("--limit", type=int, default=25)
    collect_parser = subparsers.add_parser("collect-once")
    collect_parser.add_argument("--limit", type=int, default=5)
    collect_parser.add_argument("--retry-failed", action="store_true")
    jobs_parser = subparsers.add_parser("list-jobs")
    jobs_parser.add_argument("--limit", type=int, default=25)
    datasets_parser = subparsers.add_parser("list-datasets")
    datasets_parser.add_argument("--limit", type=int, default=25)
    subparsers.add_parser("stats")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db(args.db)
        print(f"initialized data tables: {args.db}")
        return

    if args.command == "plan-once":
        result = plan_once(args.db, limit=args.limit)
        print(_format_result(result))
        return

    if args.command == "collect-once":
        result = collect_once(args.db, data_dir=args.data_dir, limit=args.limit, retry_failed=args.retry_failed)
        print(_format_result(result))
        return

    if args.command == "list-jobs":
        init_db(args.db)
        with connect(args.db) as connection:
            rows = DataRepository(connection).list_jobs(limit=args.limit)
        if not rows:
            print("no data jobs found")
            return
        for row in rows:
            error = f" | error={row['error']}" if row["error"] else ""
            print(
                f"{row['updated_at']} | {row['status']} | {row['dataset_type']} | "
                f"{row['symbol']} | {row['interval']} | {row['provider']}{error}"
            )
        return

    if args.command == "list-datasets":
        init_db(args.db)
        with connect(args.db) as connection:
            rows = DataRepository(connection).list_datasets(limit=args.limit)
        if not rows:
            print("no market datasets found")
            return
        for row in rows:
            print(
                f"{row['updated_at']} | {row['dataset_type']} | {row['symbol']} | "
                f"{row['timeframe']} | rows={row['row_count']} | {row['path']}"
            )
        return

    if args.command == "stats":
        init_db(args.db)
        with connect(args.db) as connection:
            repo = DataRepository(connection)
            print(f"data_jobs={repo.count_table('data_jobs')}")
            print(f"market_datasets={repo.count_table('market_datasets')}")
        return


def _format_result(result: dict[str, int]) -> str:
    return " | ".join(f"{key}={value}" for key, value in result.items())
