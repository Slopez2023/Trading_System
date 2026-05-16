from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Protocol

from .models import ResearchRecord
from .utils import from_json


STRATEGY_TERMS = {
    "arbitrage",
    "backtest",
    "breakout",
    "carry",
    "edge",
    "fade",
    "funding",
    "hedge",
    "mean reversion",
    "momentum",
    "pairs",
    "reversal",
    "seasonality",
    "signal",
    "spread",
    "trend",
    "volatility",
}

RISK_TERMS = {
    "drawdown",
    "fee",
    "fees",
    "illiquid",
    "latency",
    "leverage",
    "liquidation",
    "overfit",
    "risk",
    "slippage",
    "survivorship",
}

DATA_TERMS = {
    "api",
    "dataset",
    "data",
    "filing",
    "funding rate",
    "historical",
    "open interest",
    "order book",
    "short interest",
    "tick",
}

MARKET_KEYWORDS = {
    "crypto": {"btc", "bitcoin", "eth", "ethereum", "coinbase", "binance", "token", "defi", "perp"},
    "stocks": {"stock", "equity", "earnings", "nasdaq", "nyse", "sec", "small-cap"},
    "options": {"option", "iv", "implied volatility", "gamma", "delta", "put", "call"},
    "futures": {"futures", "cme", "gold", "oil", "natgas", "contract"},
    "forex": {"fx", "forex", "usd", "eur", "jpy", "gbp"},
}

ASSET_PATTERN = re.compile(r"\b[A-Z]{2,6}\b")


@dataclass(frozen=True)
class ExtractionResult:
    relevance_score: float
    records: list[ResearchRecord]


class ResearchExtractor(Protocol):
    def extract(self, raw_item: sqlite3.Row) -> ExtractionResult:
        raise NotImplementedError


class LocalResearchExtractor:
    """Rule-based extractor used until an LLM provider is plugged in."""

    def extract(self, raw_item: sqlite3.Row) -> ExtractionResult:
        title = raw_item["title"].strip()
        text = raw_item["text"].strip()
        combined = f"{title}\n{text}".strip()
        lowered = combined.lower()
        source_markets = from_json(raw_item["source_markets_json"], [])

        markets = sorted(set(source_markets + _detect_markets(lowered)))
        tags = sorted(_detect_tags(lowered))
        assets = _detect_assets(combined)
        required_data = _detect_required_data(lowered)
        risks = _detect_risks(lowered)
        relevance_score = _score_relevance(lowered, tags, markets)

        if relevance_score < 0.25:
            return ExtractionResult(relevance_score=relevance_score, records=[])

        records: list[ResearchRecord] = []
        record_type = _record_type(lowered)
        priority = _priority_score(relevance_score, len(required_data), len(markets), len(risks))
        summary = _summary(title, text)

        records.append(
            ResearchRecord(
                record_type=record_type,
                title=_record_title(record_type, title),
                summary=summary,
                details=combined[:2000],
                markets=markets,
                assets=assets,
                timeframes=_detect_timeframes(lowered),
                tags=tags,
                required_data=required_data,
                risks=risks,
                scores={
                    "priority": priority,
                    "relevance": int(relevance_score * 100),
                    "testability": _testability_score(required_data, record_type),
                    "confidence": min(70, 35 + int(relevance_score * 40)),
                },
                next_loop_targets=_next_loop_targets(record_type, required_data),
                evidence_summary=summary,
                evidence_relationship="source_observation",
            )
        )

        if required_data and record_type != "data_source":
            records.append(
                ResearchRecord(
                    record_type="research_question",
                    title=f"What data is needed to test: {title[:90]}",
                    summary=f"Potential data requirement found: {', '.join(required_data[:5])}.",
                    markets=markets,
                    assets=assets,
                    tags=sorted(set(tags + ["data_needed"])),
                    required_data=required_data,
                    scores={"priority": max(40, priority - 10), "confidence": 50},
                    next_loop_targets=["data_collection_loop"],
                    evidence_summary="Created because the source mentions data needed for possible research.",
                    evidence_relationship="derived_data_need",
                )
            )

        return ExtractionResult(relevance_score=relevance_score, records=records)


def _detect_markets(lowered: str) -> list[str]:
    markets = []
    for market, keywords in MARKET_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            markets.append(market)
    return markets


def _detect_tags(lowered: str) -> set[str]:
    tags: set[str] = set()
    for term in STRATEGY_TERMS | RISK_TERMS | DATA_TERMS:
        if term in lowered:
            tags.add(term.replace(" ", "_"))
    return tags


def _detect_assets(text: str) -> list[str]:
    assets = []
    ignored = {"API", "SEC", "RSS", "USD", "CEO", "CFO", "ETF"}
    for match in ASSET_PATTERN.findall(text):
        if match not in ignored and match not in assets:
            assets.append(match)
    return assets[:10]


def _detect_required_data(lowered: str) -> list[str]:
    data = []
    mapping = {
        "funding": "funding_rates",
        "funding rate": "funding_rates",
        "open interest": "open_interest",
        "order book": "order_book",
        "short interest": "short_interest",
        "earnings": "earnings_calendar",
        "filing": "sec_filings",
        "historical": "historical_prices",
        "tick": "tick_data",
        "volume": "price_volume",
        "volatility": "volatility_metrics",
    }
    for term, normalized in mapping.items():
        if term in lowered and normalized not in data:
            data.append(normalized)
    if not data and any(term in lowered for term in STRATEGY_TERMS):
        data.extend(["price", "volume"])
    return data


def _detect_risks(lowered: str) -> list[str]:
    risks = []
    mapping = {
        "fee": "fees may erase edge",
        "fees": "fees may erase edge",
        "slippage": "slippage may erase edge",
        "illiquid": "liquidity may be insufficient",
        "overfit": "overfitting risk",
        "survivorship": "survivorship bias risk",
        "leverage": "leverage can amplify losses",
        "liquidation": "liquidation cascade risk",
        "latency": "latency sensitivity risk",
    }
    for term, risk in mapping.items():
        if term in lowered and risk not in risks:
            risks.append(risk)
    return risks


def _detect_timeframes(lowered: str) -> list[str]:
    frames = []
    if any(term in lowered for term in ["intraday", "minute", "hourly", "scalp"]):
        frames.append("intraday")
    if any(term in lowered for term in ["daily", "swing", "overnight"]):
        frames.append("1D")
    if any(term in lowered for term in ["weekly", "seasonality", "month"]):
        frames.append("multi_day")
    return frames or ["unknown"]


def _score_relevance(lowered: str, tags: set[str], markets: list[str]) -> float:
    score = 0.05
    score += min(0.45, len(tags) * 0.06)
    score += min(0.2, len(markets) * 0.08)
    if "?" in lowered:
        score += 0.05
    if any(term in lowered for term in STRATEGY_TERMS):
        score += 0.25
    if any(term in lowered for term in DATA_TERMS):
        score += 0.1
    return min(score, 1.0)


def _record_type(lowered: str) -> str:
    if any(term in lowered for term in STRATEGY_TERMS):
        return "strategy_idea"
    if any(term in lowered for term in ["source", "dataset", "api"]):
        return "data_source"
    if any(term in lowered for term in ["risk", "drawdown", "slippage", "overfit"]):
        return "risk_warning"
    if any(term in lowered for term in ["why", "does", "can you", "how do"]):
        return "research_question"
    return "market_observation"


def _priority_score(relevance_score: float, data_count: int, market_count: int, risk_count: int) -> int:
    score = int(relevance_score * 70)
    score += min(15, data_count * 5)
    score += min(10, market_count * 4)
    score -= min(10, risk_count * 2)
    return max(1, min(score, 100))


def _testability_score(required_data: list[str], record_type: str) -> int:
    if record_type == "strategy_idea" and required_data:
        return 75
    if required_data:
        return 60
    return 35


def _next_loop_targets(record_type: str, required_data: list[str]) -> list[str]:
    targets = []
    if required_data:
        targets.append("data_collection_loop")
    if record_type == "strategy_idea":
        targets.append("backtest_loop")
    elif record_type in {"market_observation", "market_theme"}:
        targets.append("market_monitoring_loop")
    elif record_type == "risk_warning":
        targets.append("risk_review_loop")
    elif record_type == "data_source":
        targets.append("source_review_loop")
    return targets or ["human_review_loop"]


def _record_title(record_type: str, title: str) -> str:
    prefix = {
        "strategy_idea": "Strategy idea",
        "market_observation": "Market observation",
        "research_question": "Research question",
        "risk_warning": "Risk warning",
        "data_source": "Data source",
    }.get(record_type, record_type.replace("_", " ").title())
    return f"{prefix}: {title[:120]}"


def _summary(title: str, text: str) -> str:
    body = " ".join(text.split())
    if body:
        return body[:500]
    return title[:500]
