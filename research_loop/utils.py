from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def to_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def from_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def content_hash(*parts: str | None) -> str:
    payload = "\n".join(part or "" for part in parts).strip()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    lowered = value.lower()
    cleaned = []
    previous_dash = False
    for char in lowered:
        if char.isalnum():
            cleaned.append(char)
            previous_dash = False
        elif not previous_dash:
            cleaned.append("-")
            previous_dash = True
    return "".join(cleaned).strip("-") or "item"
