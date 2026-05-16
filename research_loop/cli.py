from __future__ import annotations

import argparse
import time
from pathlib import Path

from .config import DEFAULT_DB_PATH, DEFAULT_DIGEST_DIR, Settings
from .db import connect, init_db
from .evaluation import run_extractor_eval
from .monitor import render_monitor, run_monitor
from .models import RawItem, Source
from .pipeline import collect_once, extract_once, run_once, seed_sources, write_digest
from .repository import Repository
from .utils import from_json


def main() -> None:
    parser = argparse.ArgumentParser(prog="research-loop")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--digest-dir", type=Path, default=DEFAULT_DIGEST_DIR)
    parser.add_argument("--extractor", choices=["local", "openai", "hybrid"], default=None)
    parser.add_argument("--openai-model", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db")
    subparsers.add_parser("seed-sources")
    subparsers.add_parser("collect-once")

    sources_parser = subparsers.add_parser("sources")
    sources_subparsers = sources_parser.add_subparsers(dest="sources_command", required=True)
    sources_subparsers.add_parser("list")
    sources_subparsers.add_parser("health")
    source_enable = sources_subparsers.add_parser("enable")
    source_enable.add_argument("source_id")
    source_disable = sources_subparsers.add_parser("disable")
    source_disable.add_argument("source_id")

    raw_parser = subparsers.add_parser("raw")
    raw_subparsers = raw_parser.add_subparsers(dest="raw_command", required=True)
    raw_list = raw_subparsers.add_parser("list")
    raw_list.add_argument("--status", default=None)
    raw_list.add_argument("--limit", type=int, default=25)

    extract_parser = subparsers.add_parser("extract-once")
    extract_parser.add_argument("--limit", type=int, default=50)

    run_parser = subparsers.add_parser("run-once")
    run_parser.add_argument("--limit", type=int, default=50)

    digest_parser = subparsers.add_parser("digest")
    digest_parser.add_argument("--limit", type=int, default=25)

    list_parser = subparsers.add_parser("list-records")
    list_parser.add_argument("--limit", type=int, default=20)

    add_raw_parser = subparsers.add_parser("add-raw")
    add_raw_parser.add_argument("--source-id", default="manual")
    add_raw_parser.add_argument("--title", required=True)
    add_raw_parser.add_argument("--text", required=True)
    add_raw_parser.add_argument("--url", default="")
    add_raw_parser.add_argument("--source-type", default="manual")

    subparsers.add_parser("stats")
    subparsers.add_parser("smoke-test")
    subparsers.add_parser("eval-extractor")
    monitor_parser = subparsers.add_parser("monitor")
    monitor_parser.add_argument("--refresh", type=int, default=10)
    monitor_parser.add_argument("--limit", type=int, default=10)
    monitor_parser.add_argument("--once", action="store_true")

    loop_parser = subparsers.add_parser("loop")
    loop_parser.add_argument("--sleep-seconds", type=int, default=900)
    loop_parser.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()
    settings = Settings.from_env(
        db_path=args.db,
        digest_dir=args.digest_dir,
        extractor_provider=args.extractor,
        openai_model=args.openai_model,
    )

    if args.command == "init-db":
        init_db(settings.db_path)
        print(f"initialized database: {settings.db_path}")
        return

    if args.command == "seed-sources":
        count = seed_sources(settings.db_path)
        print(f"seeded {count} sources into {settings.db_path}")
        return

    if args.command == "collect-once":
        result = collect_once(settings)
        print(_format_result(result))
        return

    if args.command == "sources":
        _sources(settings, args)
        return

    if args.command == "raw":
        _raw(settings, args)
        return

    if args.command == "extract-once":
        result = extract_once(settings, limit=args.limit)
        print(_format_result(result))
        return

    if args.command == "run-once":
        result = run_once(settings, extract_limit=args.limit)
        print(_format_result(result))
        return

    if args.command == "digest":
        path = write_digest(settings, limit=args.limit)
        print(f"wrote digest: {path}")
        return

    if args.command == "list-records":
        _list_records(settings, limit=args.limit)
        return

    if args.command == "add-raw":
        _add_raw(
            settings,
            source_id=args.source_id,
            source_type=args.source_type,
            title=args.title,
            text=args.text,
            url=args.url,
        )
        return

    if args.command == "stats":
        _stats(settings)
        return

    if args.command == "smoke-test":
        _smoke_test(settings)
        return

    if args.command == "eval-extractor":
        _, lines = run_extractor_eval(settings)
        for line in lines:
            print(line)
        return

    if args.command == "monitor":
        if args.once:
            print(render_monitor(settings, limit=args.limit))
        else:
            run_monitor(settings, refresh_seconds=args.refresh, limit=args.limit)
        return

    if args.command == "loop":
        _loop(settings, sleep_seconds=args.sleep_seconds, limit=args.limit)
        return


def _loop(settings: Settings, sleep_seconds: int, limit: int) -> None:
    print(f"starting research loop with db={settings.db_path}")
    while True:
        result = run_once(settings, extract_limit=limit)
        print(_format_result(result))
        time.sleep(sleep_seconds)


def _list_records(settings: Settings, limit: int) -> None:
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        repo = Repository(connection)
        rows = repo.recent_research_records(limit=limit)
    if not rows:
        print("no research records found")
        return
    for row in rows:
        scores = from_json(row["scores_json"], {})
        markets = ", ".join(from_json(row["markets_json"], [])) or "unknown"
        print(f"{row['created_at']} | {scores.get('priority', 'n/a'):>3} | {row['record_type']} | {markets} | {row['title']}")


def _sources(settings: Settings, args) -> None:
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        repo = Repository(connection)
        if args.sources_command in {"list", "health"}:
            rows = repo.list_sources()
            if not rows:
                print("no sources found")
                return
            for row in rows:
                error = f" | error={row['last_error']}" if row["last_error"] else ""
                print(
                    f"{row['source_id']} | {row['source_type']} | {row['status']} | "
                    f"every={row['check_frequency_minutes']}m | checked={row['last_checked_at'] or 'never'} | "
                    f"failures={row['failure_count']}{error}"
                )
            return
        if args.sources_command == "enable":
            updated = repo.set_source_status(args.source_id, "active")
        elif args.sources_command == "disable":
            updated = repo.set_source_status(args.source_id, "disabled")
        else:
            updated = False
        connection.commit()
    print(f"updated={int(updated)}")


def _raw(settings: Settings, args) -> None:
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        repo = Repository(connection)
        rows = repo.list_raw_items(status=args.status, limit=args.limit)
    if not rows:
        print("no raw items found")
        return
    for row in rows:
        error = f" | error={row['processing_error']}" if row["processing_error"] else ""
        print(
            f"{row['raw_item_id']} | {row['processing_status']} | {row['source_id']} | "
            f"relevance={row['relevance_score']} | {row['title']}{error}"
        )


def _add_raw(settings: Settings, source_id: str, source_type: str, title: str, text: str, url: str) -> None:
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        repo = Repository(connection)
        existing = connection.execute(
            "SELECT source_id FROM sources WHERE source_id = ?",
            (source_id,),
        ).fetchone()
        if existing is None:
            repo.upsert_source(
                Source(
                    source_id=source_id,
                    source_type=source_type,
                    name="Manual research input" if source_id == "manual" else source_id,
                    url=f"manual://{source_id}",
                    markets=[],
                    topics=["manual", "research"],
                    status="disabled" if source_type == "manual" else "active",
                    check_frequency_minutes=0,
                    quality_score=0.8,
                    noise_score=0.2,
                )
            )
        inserted = repo.insert_raw_items(
            [
                RawItem(
                    source_id=source_id,
                    source_type=source_type,
                    url=url,
                    title=title,
                    text=text,
                    metadata={"collector": "manual"},
                )
            ]
        )
        connection.commit()
    print(f"raw_items_inserted={inserted}")


def _stats(settings: Settings) -> None:
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        repo = Repository(connection)
        print(f"sources={repo.count_table('sources')}")
        print(f"raw_items={repo.count_table('raw_items')}")
        print(f"research_records={repo.count_table('research_records')}")
        print(f"evidence_links={repo.count_table('evidence_links')}")


def _smoke_test(settings: Settings) -> None:
    init_db(settings.db_path)
    _add_raw(
        settings,
        source_id="manual_smoke",
        source_type="manual",
        title="BTC funding spike reversal smoke test",
        text="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike. Watch slippage.",
        url="manual://smoke-test",
    )
    result = extract_once(settings, limit=5)
    print(_format_result(result))
    _list_records(settings, limit=5)
    path = write_digest(settings, limit=5)
    print(f"digest={path}")


def _format_result(result: dict[str, int]) -> str:
    return " | ".join(f"{key}={value}" for key, value in result.items())
