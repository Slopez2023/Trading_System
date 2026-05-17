from __future__ import annotations

import argparse
from pathlib import Path

from research_loop.config import DEFAULT_DB_PATH
from research_loop.db import connect
from research_loop.utils import from_json

from .db import init_db
from .planner import plan_once
from .repository import ExperimentRepository


def main() -> None:
    parser = argparse.ArgumentParser(prog="experiment-loop")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db")
    plan_parser = subparsers.add_parser("plan-once")
    plan_parser.add_argument("--limit", type=int, default=5)
    plan_parser.add_argument("--min-roi", type=int, default=20)
    list_parser = subparsers.add_parser("list-specs")
    list_parser.add_argument("--limit", type=int, default=20)
    subparsers.add_parser("stats")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db(args.db)
        print(f"initialized experiment tables: {args.db}")
        return

    if args.command == "plan-once":
        init_db(args.db)
        with connect(args.db) as connection:
            result = plan_once(connection, limit=args.limit, min_roi=args.min_roi)
        print(_format_result(result))
        return

    if args.command == "list-specs":
        init_db(args.db)
        with connect(args.db) as connection:
            repo = ExperimentRepository(connection)
            rows = repo.recent_experiment_specs(limit=args.limit)
        if not rows:
            print("no experiment specs found")
            return
        for row in rows:
            scores = from_json(row["scores_json"], {})
            print(
                f"{row['updated_at']} | {scores.get('roi', 'n/a'):>3} | "
                f"{row['experiment_type']} | {row['status']} | {row['thesis']}"
            )
        return

    if args.command == "stats":
        init_db(args.db)
        with connect(args.db) as connection:
            repo = ExperimentRepository(connection)
            print(f"experiment_specs={repo.count_table('experiment_specs')}")
            print(f"experiment_data_requirements={repo.count_table('experiment_data_requirements')}")
        return


def _format_result(result: dict[str, int]) -> str:
    return " | ".join(f"{key}={value}" for key, value in result.items())
