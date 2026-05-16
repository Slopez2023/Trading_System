from __future__ import annotations

import re

from .models import ResearchRecord
from .utils import content_hash


STOPWORDS = {
    "a",
    "an",
    "and",
    "after",
    "before",
    "for",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def record_fingerprint(record: ResearchRecord) -> str:
    """Conservative fingerprint for obvious duplicate research records."""
    key_terms = _concept_terms(record)
    market_terms = _market_terms(record.markets)
    asset_terms = sorted(_normalize_token(asset) for asset in record.assets if asset)
    data_terms = sorted(_data_concepts(record.required_data))
    payload = "|".join(
        [
            record.record_type,
            " ".join(key_terms[:12]),
            " ".join(market_terms[:6]),
            " ".join(asset_terms[:6]),
            " ".join(data_terms[:8]),
        ]
    )
    return content_hash(payload)


def _key_terms(record: ResearchRecord) -> list[str]:
    text = " ".join([record.title, record.summary, " ".join(record.tags)]).lower()
    tokens = []
    for token in re.findall(r"[a-z0-9]+", text):
        if token in STOPWORDS or len(token) < 3:
            continue
        normalized = _normalize_token(token)
        if normalized and normalized not in tokens:
            tokens.append(normalized)
    return tokens


def _concept_terms(record: ResearchRecord) -> list[str]:
    text = " ".join([record.title, record.summary, " ".join(record.tags), " ".join(record.required_data)]).lower()
    concepts = []
    concept_map = {
        "btc": ["btc", "bitcoin"],
        "eth": ["eth", "ethereum"],
        "sol": ["sol", "solana"],
        "funding": ["funding", "funding rates", "funding rate"],
        "open_interest": ["open interest", "oi"],
        "reversal": ["reversal", "reverse", "mean reversion"],
        "momentum": ["momentum", "trend"],
        "listing": ["listing", "listings", "coinbase", "binance"],
        "bridge": ["bridge", "bridging"],
        "arbitrage": ["arbitrage", "arb"],
        "fees": ["fee", "fees"],
        "earnings": ["earnings"],
        "volume": ["volume"],
    }
    for concept, needles in concept_map.items():
        if any(_contains_term(text, needle) for needle in needles):
            concepts.append(concept)
    if concepts:
        return concepts
    return _key_terms(record)


def _data_concepts(values: list[str]) -> list[str]:
    text = " ".join(values).lower()
    concepts = []
    concept_map = {
        "funding": ["funding", "funding_rates", "funding rate"],
        "open_interest": ["open interest", "open_interest", "oi"],
        "price_volume": ["price_volume", "price", "volume"],
        "liquidations": ["liquidation", "liquidations"],
        "listing_timestamps": ["listing", "announcement", "timestamp"],
    }
    for concept, needles in concept_map.items():
        if any(needle in text for needle in needles):
            concepts.append(concept)
    return concepts or [_normalize_token(item) for item in values if item]


def _market_terms(values: list[str]) -> list[str]:
    terms = sorted(_normalize_token(market) for market in values if market)
    if "crypto" in terms:
        return ["crypto"]
    return terms


def _contains_term(text: str, term: str) -> bool:
    if " " in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def _normalize_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    aliases = {
        "bitcoin": "btc",
        "perpetual": "perp",
        "perpetuals": "perp",
        "futures": "futures",
        "open": "open",
        "open_interest": "oi",
        "interest": "interest",
        "funding_rates": "funding",
        "funding_rate": "funding",
        "price_volume": "price_volume",
        "coinbase": "coinbase",
        "binance": "binance",
    }
    return aliases.get(token, token)
