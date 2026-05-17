from __future__ import annotations

import json

from research_loop.event_log import append_event


def test_append_event_writes_jsonl(tmp_path) -> None:
    log_path = tmp_path / "logs" / "research_loop.jsonl"

    append_event(log_path, "run_once", {"records_created": 2})

    lines = log_path.read_text(encoding="utf-8").splitlines()
    event = json.loads(lines[0])
    assert event["event"] == "run_once"
    assert event["records_created"] == 2
    assert "ts" in event
