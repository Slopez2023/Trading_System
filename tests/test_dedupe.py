from __future__ import annotations

from research_loop.dedupe import record_fingerprint
from research_loop.models import ResearchRecord


def test_record_fingerprint_matches_obvious_duplicates() -> None:
    first = ResearchRecord(
        record_type="strategy_idea",
        title="BTC funding OI reversal",
        summary="Backtest BTC perpetual futures reversal after funding and open interest spike.",
        markets=["crypto"],
        required_data=["funding rates", "open interest"],
    )
    second = ResearchRecord(
        record_type="strategy_idea",
        title="BTC funding open interest reversal strategy",
        summary="Test BTC perps after funding and OI spikes.",
        markets=["crypto"],
        required_data=["funding rates", "open interest"],
    )

    assert record_fingerprint(first) == record_fingerprint(second)


def test_record_fingerprint_matches_crypto_perp_market_aliases() -> None:
    first = ResearchRecord(
        record_type="strategy_idea",
        title="BTC funding squeeze reversal",
        summary="Short BTC after an extreme positive funding spike fades.",
        markets=["BTC/USDT perpetual futures", "crypto"],
        assets=["BTC"],
        required_data=[
            "BTC perpetual funding rate history",
            "BTC/USDT price data",
        ],
    )
    second = ResearchRecord(
        record_type="strategy_idea",
        title="BTC funding rate reversal short",
        summary="Short BTCUSDT perpetuals after crowded positive funding rejects.",
        markets=["BTCUSDT perpetual"],
        assets=["BTC"],
        required_data=[
            "BTC perpetual funding rate",
            "BTCUSDT perpetual price candles",
        ],
    )

    assert record_fingerprint(first) == record_fingerprint(second)


def test_record_fingerprint_does_not_merge_different_record_types() -> None:
    strategy = ResearchRecord(
        record_type="strategy_idea",
        title="Bridge arbitrage fee risk",
        summary="Hidden fees can break bridge arbitrage.",
        markets=["crypto"],
    )
    warning = ResearchRecord(
        record_type="risk_warning",
        title="Bridge arbitrage fee risk",
        summary="Hidden fees can break bridge arbitrage.",
        markets=["crypto"],
    )

    assert record_fingerprint(strategy) != record_fingerprint(warning)
