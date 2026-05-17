from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import to_json, utc_now


def append_event(log_path: Path, event_type: str, payload: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": utc_now(),
        "event": event_type,
        **payload,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(to_json(event) + "\n")
