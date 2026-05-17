from __future__ import annotations

from dataclasses import replace

from .models import ResearchRecord


ALLOWED_LOOP_TARGETS = {
    "data_collection_loop",
    "backtest_loop",
    "risk_review_loop",
    "market_monitoring_loop",
    "source_review_loop",
    "human_review_loop",
}

MARKET_ALIASES = {
    "btc perpetual futures": "crypto",
    "perpetual futures": "crypto",
    "coinbase": "crypto",
    "binance": "crypto",
    "dex": "crypto",
    "defi": "crypto",
    "bridge": "crypto",
    "etf": "stocks",
    "earnings": "stocks",
    "options": "options",
}

BROAD_MARKETS = {"crypto", "forex", "futures", "options", "stocks"}

SCORE_KEYS = {
    "priority",
    "novelty",
    "testability",
    "data_availability",
    "urgency",
    "confidence",
    "source_quality",
}


def normalize_record(record: ResearchRecord) -> ResearchRecord:
    required_data = _clean_list(record.required_data)
    risks = _clean_list(record.risks)
    tags = _clean_list(record.tags)
    markets = _normalize_markets(record)
    targets, moved_data = _normalize_targets(record.next_loop_targets)
    required_data = _merge(required_data, moved_data)

    if record.record_type == "strategy_idea":
        if required_data:
            targets = _merge(targets, ["data_collection_loop"])
        targets = _merge(targets, ["backtest_loop"])
    elif record.record_type == "risk_warning":
        targets = _merge(targets, ["risk_review_loop"])
        risks = risks or _risks_from_text(record)
    elif record.record_type == "data_source":
        targets = _merge(targets, ["source_review_loop", "data_collection_loop"])
    elif record.record_type in {"market_observation", "market_theme", "anomaly", "event_catalyst"}:
        targets = _merge(targets, ["market_monitoring_loop"])
    elif record.record_type == "research_question":
        targets = _merge(targets, ["human_review_loop"])
        if required_data:
            targets = _merge(targets, ["data_collection_loop"])

    status = _status(record, required_data, risks, targets)
    scores = _normalize_scores(record.scores, record.record_type)

    return replace(
        record,
        markets=markets,
        required_data=required_data,
        risks=risks,
        tags=tags,
        next_loop_targets=targets or ["human_review_loop"],
        status=status,
        scores=scores,
    )


def normalize_records(records: list[ResearchRecord]) -> list[ResearchRecord]:
    return [normalize_record(record) for record in records]


def _normalize_targets(targets: list[str]) -> tuple[list[str], list[str]]:
    valid = []
    moved_data = []
    for target in _clean_list(targets):
        if target in ALLOWED_LOOP_TARGETS:
            valid.append(target)
        else:
            moved_data.append(target)
    return valid, moved_data


def _normalize_markets(record: ResearchRecord) -> list[str]:
    markets = _clean_list(record.markets)
    text = " ".join(
        [
            record.title,
            record.summary,
            record.details,
            " ".join(record.assets),
            " ".join(record.tags),
        ]
    ).lower()
    inferred = []
    for needle, market in MARKET_ALIASES.items():
        if needle in text:
            inferred.append(market)
    inferred = _clean_list(inferred)
    broad_markets = [market for market in markets if market in BROAD_MARKETS]
    if len(broad_markets) >= 4 and len(broad_markets) == len(markets):
        return inferred
    if inferred and len(broad_markets) >= 2 and len(broad_markets) == len(markets):
        return inferred
    return _clean_list([*markets, *inferred])


def _status(record: ResearchRecord, required_data: list[str], risks: list[str], targets: list[str]) -> str:
    if record.record_type == "risk_warning":
        return "risk_only"
    if required_data and "data_collection_loop" in targets:
        return "needs_data"
    if record.record_type == "strategy_idea" and "backtest_loop" in targets:
        priority = int(record.scores.get("priority", 0) or 0)
        confidence = int(record.scores.get("confidence", 0) or 0)
        if priority >= 65 and confidence >= 45:
            return "ready_for_backtest"
    if _looks_weird(record):
        return "weird_but_interesting"
    return "needs_review"


def _normalize_scores(scores: dict[str, int], record_type: str) -> dict[str, int]:
    normalized = _score_defaults(record_type)
    for key, value in scores.items():
        try:
            normalized[key] = max(0, min(int(value), 100))
        except (TypeError, ValueError):
            continue
    if "priority" not in normalized:
        normalized["priority"] = 50 if record_type == "strategy_idea" else 35
    if "confidence" not in normalized:
        normalized["confidence"] = 50
    if record_type == "risk_warning":
        normalized["priority"] = max(normalized.get("priority", 0), 60)
        normalized["confidence"] = max(normalized.get("confidence", 0), 50)
        normalized["urgency"] = max(normalized.get("urgency", 0), 50)
        normalized["testability"] = max(normalized.get("testability", 0), 20)
    if record_type == "strategy_idea":
        normalized["priority"] = max(normalized.get("priority", 0), 45)
        normalized["testability"] = max(normalized.get("testability", 0), 45)
    for key in SCORE_KEYS:
        normalized.setdefault(key, 50)
    return normalized


def _score_defaults(record_type: str) -> dict[str, int]:
    defaults = {
        "priority": 35,
        "novelty": 45,
        "testability": 35,
        "data_availability": 40,
        "urgency": 35,
        "confidence": 50,
        "source_quality": 50,
    }
    if record_type == "strategy_idea":
        defaults.update({"priority": 50, "testability": 55, "data_availability": 45})
    elif record_type == "risk_warning":
        defaults.update({"priority": 60, "testability": 20, "urgency": 55})
    elif record_type == "data_source":
        defaults.update({"priority": 45, "testability": 40, "data_availability": 70})
    elif record_type == "event_catalyst":
        defaults.update({"priority": 50, "urgency": 60})
    return defaults


def _risks_from_text(record: ResearchRecord) -> list[str]:
    text = f"{record.title} {record.summary} {record.details}".lower()
    risks = []
    mapping = {
        "hidden fee": "hidden fees may erase edge",
        "fee": "fees may erase edge",
        "slippage": "slippage may erase edge",
        "liquidity": "liquidity may be insufficient",
        "slow settlement": "slow settlement may break execution assumptions",
        "liquidation": "liquidation risk",
    }
    for needle, risk in mapping.items():
        if needle in text:
            risks.append(risk)
    return _clean_list(risks)


def _looks_weird(record: ResearchRecord) -> bool:
    text = f"{record.title} {record.summary} {' '.join(record.tags)}".lower()
    return any(term in text for term in ["weird", "unusual", "strange", "niche", "rumor"])


def _merge(first: list[str], second: list[str]) -> list[str]:
    return _clean_list([*first, *second])


def _clean_list(values: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        cleaned.append(item)
        seen.add(item)
    return cleaned
