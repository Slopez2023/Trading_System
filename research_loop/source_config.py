from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import Source


ALLOWED_SOURCE_TYPES = {"rss", "reddit", "manual"}
ALLOWED_STATUSES = {"active", "disabled", "candidate"}
ALLOWED_CATEGORIES = {"social", "news", "exchange", "research", "market_data", "filing", "manual"}


class SourceConfigError(ValueError):
    pass


def load_source_config(path: Path | str) -> list[Source]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SourceConfigError("source config must be a JSON object")
    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list):
        raise SourceConfigError("source config must contain a sources list")
    return [source_from_config(item, index=index) for index, item in enumerate(raw_sources, start=1)]


def write_source_config(path: Path | str, sources: list[Source]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "sources": [source_to_config(source) for source in sources],
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def source_from_config(item: Any, index: int = 0) -> Source:
    if not isinstance(item, dict):
        raise SourceConfigError(f"source #{index} must be an object")

    source_id = _required_str(item, "source_id", index)
    source_type = _required_str(item, "source_type", index)
    name = _required_str(item, "name", index)
    url = _required_str(item, "url", index)
    status = str(item.get("status", "active")).strip().lower()
    category = str(item.get("category", item.get("metadata", {}).get("category", ""))).strip().lower()

    if source_type not in ALLOWED_SOURCE_TYPES:
        raise SourceConfigError(f"{source_id}: unsupported source_type '{source_type}'")
    if status not in ALLOWED_STATUSES:
        raise SourceConfigError(f"{source_id}: unsupported status '{status}'")
    if category and category not in ALLOWED_CATEGORIES:
        raise SourceConfigError(f"{source_id}: unsupported category '{category}'")
    if source_type in {"rss", "reddit"} and not url.startswith(("http://", "https://")):
        raise SourceConfigError(f"{source_id}: {source_type} sources require an http(s) url")

    metadata = dict(item.get("metadata", {}))
    if category:
        metadata["category"] = category
    return Source(
        source_id=source_id,
        source_type=source_type,
        name=name,
        url=url,
        markets=_string_list(item.get("markets", []), "markets", source_id),
        topics=_string_list(item.get("topics", []), "topics", source_id),
        status=status,
        check_frequency_minutes=_positive_int(item.get("check_frequency_minutes", 60), "check_frequency_minutes", source_id),
        quality_score=_score(item.get("quality_score", 0.5), "quality_score", source_id),
        noise_score=_score(item.get("noise_score", 0.5), "noise_score", source_id),
        metadata=metadata,
    )


def source_to_config(source: Source) -> dict[str, Any]:
    payload = asdict(source)
    metadata = dict(payload.pop("metadata") or {})
    category = metadata.pop("category", "")
    if category:
        payload["category"] = category
    if metadata:
        payload["metadata"] = metadata
    return payload


def _required_str(item: dict[str, Any], key: str, index: int) -> str:
    value = str(item.get(key, "")).strip()
    if not value:
        raise SourceConfigError(f"source #{index} missing required field '{key}'")
    return value


def _string_list(value: Any, field: str, source_id: str) -> list[str]:
    if not isinstance(value, list):
        raise SourceConfigError(f"{source_id}: {field} must be a list")
    cleaned = []
    for item in value:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def _positive_int(value: Any, field: str, source_id: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SourceConfigError(f"{source_id}: {field} must be an integer") from exc
    if number < 0:
        raise SourceConfigError(f"{source_id}: {field} must be zero or greater")
    return number


def _score(value: Any, field: str, source_id: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SourceConfigError(f"{source_id}: {field} must be a number") from exc
    if number < 0 or number > 1:
        raise SourceConfigError(f"{source_id}: {field} must be between 0 and 1")
    return number
