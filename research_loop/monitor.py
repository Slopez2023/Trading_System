from __future__ import annotations

import os
import time
from datetime import datetime

from .config import Settings
from .db import connect, init_db
from .repository import Repository
from .utils import from_json


def run_monitor(settings: Settings, refresh_seconds: int = 10, limit: int = 10) -> None:
    try:
        while True:
            print(render_monitor(settings, limit=limit), flush=True)
            time.sleep(refresh_seconds)
    except KeyboardInterrupt:
        print("\nmonitor stopped")


def render_monitor(settings: Settings, limit: int = 10) -> str:
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        repo = Repository(connection)
        source_counts = repo.source_status_counts()
        raw_counts = repo.raw_status_counts()
        record_counts = repo.record_type_counts()
        latest_records = repo.recent_research_records(limit=limit)
        latest_errors = repo.latest_source_errors(limit=5)

    lines = [_clear_screen()]
    lines.extend(
        [
            "Trading Research Loop Monitor",
            "=" * 72,
            f"Time:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"DB:        {settings.db_path}",
            f"Extractor: {settings.extractor_provider}",
            f"Model:     {_model_label(settings)}",
            "",
            _section("Sources"),
            _kv_line(
                [
                    ("active", source_counts.get("active", 0)),
                    ("disabled", source_counts.get("disabled", 0)),
                    ("failed", _failed_sources(latest_errors)),
                    ("total", sum(source_counts.values())),
                ]
            ),
            "",
            _section("Raw Items"),
            _kv_line(
                [
                    ("pending", raw_counts.get("pending", 0)),
                    ("processing", raw_counts.get("processing", 0)),
                    ("extracted", raw_counts.get("extracted", 0)),
                    ("ignored", raw_counts.get("ignored", 0)),
                    ("failed", raw_counts.get("failed", 0)),
                ]
            ),
            "",
            _section("Research Records"),
            _record_counts_line(record_counts),
            "",
            _section(f"Latest Records ({len(latest_records)})"),
        ]
    )
    lines.extend(_latest_records(latest_records))
    lines.extend(["", _section("Last Source Errors")])
    lines.extend(_latest_errors(latest_errors))
    lines.extend(["", "Press Ctrl+C to stop."])
    return "\n".join(lines)


def _clear_screen() -> str:
    return "\033[2J\033[H" if os.getenv("TERM") else ""


def _section(title: str) -> str:
    return f"-- {title} " + "-" * max(0, 68 - len(title))


def _kv_line(items: list[tuple[str, int]]) -> str:
    return " | ".join(f"{key}: {value}" for key, value in items)


def _record_counts_line(record_counts: dict[str, int]) -> str:
    if not record_counts:
        return "total: 0"
    total = sum(record_counts.values())
    top = list(record_counts.items())[:5]
    return " | ".join([f"total: {total}"] + [f"{key}: {value}" for key, value in top])


def _latest_records(rows) -> list[str]:
    if not rows:
        return ["no records yet"]
    lines = []
    for row in rows:
        scores = from_json(row["scores_json"], {})
        priority = str(scores.get("priority", "n/a")).rjust(3)
        title = _truncate(row["title"], 54)
        lines.append(f"{priority} | {_truncate(row['record_type'], 17):17} | {title}")
    return lines


def _latest_errors(rows) -> list[str]:
    if not rows:
        return ["none"]
    lines = []
    for row in rows:
        error = _truncate(row["last_error"], 70)
        lines.append(f"{row['last_failed_at'] or 'unknown'} | {row['source_id']} | failures={row['failure_count']} | {error}")
    return lines


def _failed_sources(rows) -> int:
    return len(rows)


def _model_label(settings: Settings) -> str:
    if settings.extractor_provider == "local":
        return "local"
    return settings.openai_model


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: max(0, width - 3)] + "..."
