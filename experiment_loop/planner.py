from __future__ import annotations

import sqlite3
from typing import Any

from research_loop.utils import from_json

from .models import ExperimentSpec
from .repository import ExperimentRepository


DEFAULT_TIMEFRAMES = ["1h", "4h", "12h", "24h"]
DEFAULT_COST_MODEL = ["fees", "slippage"]


def plan_once(connection: sqlite3.Connection, limit: int = 5, min_roi: int = 20) -> dict[str, int]:
    repo = ExperimentRepository(connection)
    created_or_updated = 0
    skipped = 0
    for row in repo.candidate_research_records(limit=limit):
        spec = spec_from_research_record(row)
        if spec is None or spec.scores.get("roi", 0) < min_roi:
            skipped += 1
            continue
        if repo.insert_experiment_spec(spec):
            created_or_updated += 1
    connection.commit()
    return {
        "records_seen": created_or_updated + skipped,
        "experiment_specs_written": created_or_updated,
        "records_skipped": skipped,
    }


def spec_from_research_record(row: sqlite3.Row) -> ExperimentSpec | None:
    record_type = row["record_type"]
    title = row["title"]
    summary = row["summary"]
    details = row["details"]
    text = " ".join([title, summary, details]).lower()
    scores = from_json(row["scores_json"], {})
    markets = from_json(row["markets_json"], [])
    assets = from_json(row["assets_json"], [])
    required_data = _normalize_data_needed(from_json(row["required_data_json"], []), text)
    risks = from_json(row["risks_json"], [])

    if record_type == "risk_warning":
        return _risk_model(row, text, markets, assets, required_data, risks, scores)
    if record_type != "strategy_idea":
        return None
    if _is_too_vague(summary, required_data):
        return None
    if "listing" in text or "announcement" in text:
        return _listing_event_study(row, markets, assets, required_data, risks, scores)
    if "funding" in text and ("open interest" in text or " oi " in f" {text} "):
        return _funding_signal_backtest(row, markets, assets, required_data, risks, scores)
    return None


def _funding_signal_backtest(
    row: sqlite3.Row,
    markets: list[str],
    assets: list[str],
    required_data: list[str],
    risks: list[str],
    scores: dict[str, Any],
) -> ExperimentSpec:
    data_needed = _dedupe([*required_data, "ohlcv", "funding_rates", "open_interest", "volume"])
    return ExperimentSpec(
        source_record_id=row["record_id"],
        thesis="BTC perpetual futures may reverse after extreme funding, rising open interest, and volume spikes.",
        experiment_type="signal_backtest",
        market=_best_market(markets, "crypto perpetuals"),
        asset=_best_asset(assets, "BTC"),
        timeframes=DEFAULT_TIMEFRAMES,
        data_needed=data_needed,
        entry_rule="Enter contrarian when funding is above/below an extreme percentile and open interest plus volume are rising.",
        exit_rule="Exit after fixed holding windows and compare 1h, 4h, 12h, and 24h outcomes.",
        cost_model=DEFAULT_COST_MODEL,
        success_metric="Positive net expectancy after fees and slippage across multiple out-of-sample periods.",
        reject_if="Reject if returns disappear after costs, only work in one regime, or require liquidation-level leverage.",
        status="needs_data",
        scores=_experiment_scores(scores, data_needed, risks, clarity=85, execution_difficulty=45),
        notes="Planner recognized funding/open-interest reversal structure.",
    )


def _listing_event_study(
    row: sqlite3.Row,
    markets: list[str],
    assets: list[str],
    required_data: list[str],
    risks: list[str],
    scores: dict[str, Any],
) -> ExperimentSpec:
    data_needed = _dedupe(
        [
            *required_data,
            "listing_announcement_timestamps",
            "ohlcv",
            "volume",
            "liquidity_filters",
        ]
    )
    return ExperimentSpec(
        source_record_id=row["record_id"],
        thesis="Exchange listing announcements may create momentum before/at announcement and reversal after the initial spike.",
        experiment_type="event_study",
        market=_best_market(markets, "crypto"),
        asset=_best_asset(assets, "listed crypto assets"),
        timeframes=["1h", "4h", "1d", "7d"],
        data_needed=data_needed,
        entry_rule="Align each asset to its public Coinbase/Binance listing announcement timestamp and measure abnormal returns around the event.",
        exit_rule="Evaluate post-announcement windows and reversal windows separately.",
        cost_model=DEFAULT_COST_MODEL,
        success_metric="Statistically positive abnormal return pattern after costs with enough events and liquidity.",
        reject_if="Reject if timestamps are imprecise, sample size is too small, or edge vanishes after liquidity filters.",
        status="needs_data",
        scores=_experiment_scores(scores, data_needed, risks, clarity=80, execution_difficulty=55),
        notes="Planner recognized exchange-listing event-study structure.",
    )


def _risk_model(
    row: sqlite3.Row,
    text: str,
    markets: list[str],
    assets: list[str],
    required_data: list[str],
    risks: list[str],
    scores: dict[str, Any],
) -> ExperimentSpec | None:
    risk_text = " ".join([text, *risks]).lower()
    if not any(token in risk_text for token in ["fee", "slippage", "liquidity", "latency", "settlement", "spread"]):
        return None
    data_needed = _dedupe([*required_data, "spread", "fees", "liquidity", "execution_latency"])
    return ExperimentSpec(
        source_record_id=row["record_id"],
        thesis=row["summary"][:240],
        experiment_type="risk_model",
        market=_best_market(markets, "unknown"),
        asset=_best_asset(assets, ""),
        timeframes=[],
        data_needed=data_needed,
        entry_rule="Model the named risk as a cost or execution constraint before allowing related strategies into backtesting.",
        exit_rule="Pass/fail risk gate rather than trade exit.",
        cost_model=_dedupe([*DEFAULT_COST_MODEL, *risks]),
        success_metric="Risk can be measured and bounded with conservative assumptions.",
        reject_if="Reject related strategies if the modeled cost or delay erases expected edge.",
        status="needs_data",
        scores=_experiment_scores(scores, data_needed, risks, clarity=65, execution_difficulty=50),
        notes="Planner converted risk warning into a risk-model experiment.",
    )


def _normalize_data_needed(values: list[str], text: str) -> list[str]:
    data = _dedupe(
        [
            _canonical_data_name(value)
            for value in values
            if _looks_like_data_name(str(value))
        ]
    )
    lower_values = " ".join(data).lower()
    if "price" in lower_values and "ohlcv" not in lower_values:
        data.append("ohlcv")
    if "funding" in text and "funding_rates" not in lower_values:
        data.append("funding_rates")
    if "open interest" in text and "open_interest" not in lower_values:
        data.append("open_interest")
    return _dedupe(data)


def _canonical_data_name(value: str) -> str:
    normalized = str(value).strip().lower().replace("-", " ").replace("_", " ")
    aliases = {
        "funding rate": "funding_rates",
        "funding rates": "funding_rates",
        "funding rate history": "funding_rates",
        "open interest": "open_interest",
        "open interest history": "open_interest",
        "price": "ohlcv",
        "price data": "ohlcv",
        "price data for listed assets": "ohlcv",
        "historical prices": "ohlcv",
        "volume": "volume",
        "volume data": "volume",
        "volume data for listed assets": "volume",
        "price volume": "ohlcv",
        "price and volume data": "ohlcv",
        "tick data": "tick_data",
        "historical coinbase listing announcement timestamps": "listing_announcement_timestamps",
        "historical binance listing announcement timestamps": "listing_announcement_timestamps",
        "historical listing announcement timestamps": "listing_announcement_timestamps",
    }
    return aliases.get(normalized, str(value).strip())


def _looks_like_data_name(value: str) -> bool:
    stripped = value.strip()
    lowered = stripped.lower()
    if not stripped:
        return False
    if "." in stripped:
        return False
    if lowered.startswith(("collect ", "backtest ", "define ", "test ", "monitor ", "identify ", "compute ", "compare ")):
        return False
    return True


def _experiment_scores(
    source_scores: dict[str, Any],
    data_needed: list[str],
    risks: list[str],
    clarity: int,
    execution_difficulty: int,
) -> dict[str, int]:
    source_priority = _int_score(source_scores.get("priority"), 50)
    source_confidence = _int_score(source_scores.get("confidence"), 50)
    source_data_availability = _int_score(source_scores.get("data_availability"), 55)
    data_cost = min(90, 25 + len(data_needed) * 7)
    risk_penalty = min(30, len(risks) * 6)
    roi = round((clarity + source_data_availability + source_priority + source_confidence) / 4 - data_cost * 0.25 - execution_difficulty * 0.2 - risk_penalty)
    return {
        "roi": max(0, min(100, roi)),
        "clarity": clarity,
        "data_availability": source_data_availability,
        "data_cost": data_cost,
        "execution_difficulty": execution_difficulty,
        "source_priority": source_priority,
        "source_confidence": source_confidence,
    }


def _is_too_vague(summary: str, required_data: list[str]) -> bool:
    return len(summary.strip()) < 20 or len(required_data) == 0


def _best_market(markets: list[str], fallback: str) -> str:
    if not markets:
        return fallback
    if "crypto" in markets and len(markets) > 3:
        return "crypto"
    return str(markets[0])


def _best_asset(assets: list[str], fallback: str) -> str:
    return str(assets[0]) if assets else fallback


def _int_score(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _dedupe(values: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for value in values:
        item = str(value).strip()
        key = item.lower().replace(" ", "_")
        if not item or key in seen:
            continue
        cleaned.append(item)
        seen.add(key)
    return cleaned
