from __future__ import annotations

from research_loop.models import ResearchRecord
from research_loop.normalization import normalize_record


def test_normalizer_moves_invalid_loop_targets_to_required_data() -> None:
    record = ResearchRecord(
        record_type="strategy_idea",
        title="Exchange listing momentum",
        summary="Test Coinbase and Binance listing momentum.",
        markets=[],
        required_data=["price data"],
        scores={"priority": 70, "confidence": 60},
        next_loop_targets=["Coinbase listing API"],
    )

    normalized = normalize_record(record)

    assert "Coinbase listing API" in normalized.required_data
    assert "data_collection_loop" in normalized.next_loop_targets
    assert "backtest_loop" in normalized.next_loop_targets
    assert normalized.status == "needs_data"
    assert "crypto" in normalized.markets


def test_normalizer_routes_risk_warning_and_preserves_risk() -> None:
    record = ResearchRecord(
        record_type="risk_warning",
        title="Bridge arbitrage fee risk",
        summary="Hidden fees and unstable liquidity can break bridge arbitrage.",
        risks=[],
        next_loop_targets=[],
        scores={"priority": 75, "confidence": 80},
    )

    normalized = normalize_record(record)

    assert normalized.status == "risk_only"
    assert "risk_review_loop" in normalized.next_loop_targets
    assert normalized.risks
    assert "crypto" in normalized.markets
    assert normalized.scores["priority"] >= 60


def test_normalizer_marks_ready_strategy_without_data_gap() -> None:
    record = ResearchRecord(
        record_type="strategy_idea",
        title="BTC funding reversal",
        summary="Backtest BTC perpetual futures funding reversal.",
        markets=["crypto"],
        required_data=[],
        scores={"priority": 80, "confidence": 55},
    )

    normalized = normalize_record(record)

    assert normalized.status == "ready_for_backtest"
    assert "backtest_loop" in normalized.next_loop_targets
