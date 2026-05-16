from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .config import Settings
from .extraction import ExtractionResult, ResearchExtractor
from .pipeline import _extractor


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    title: str
    text: str
    source_markets_json: str
    source_topics_json: str
    expected_types: set[str]
    expected_markets: set[str]
    expected_required_data: set[str]
    expected_routes: set[str]


EVAL_CASES = [
    EvalCase(
        case_id="btc_funding_reversal",
        title="BTC funding spike reversal",
        text="Backtest whether BTC perpetual futures reverse after funding rates and open interest spike with high volume. Watch slippage and liquidation risk.",
        source_markets_json='["crypto", "futures"]',
        source_topics_json='["funding", "open_interest"]',
        expected_types={"strategy_idea", "research_question"},
        expected_markets={"crypto", "futures"},
        expected_required_data={"funding_rates", "open_interest", "price_volume"},
        expected_routes={"backtest_loop", "data_collection_loop"},
    ),
    EvalCase(
        case_id="bridge_fee_warning",
        title="Hidden DEX bridge fee warning",
        text="A bridge route shows high hidden fees and unstable liquidity. This is mainly a risk warning for arbitrage strategies that depend on fast bridge execution.",
        source_markets_json='["crypto"]',
        source_topics_json='["risk", "fees"]',
        expected_types={"risk_warning"},
        expected_markets={"crypto"},
        expected_required_data=set(),
        expected_routes={"risk_review_loop"},
    ),
    EvalCase(
        case_id="listing_dataset_need",
        title="Need exchange listing announcement dataset",
        text="Find a data source or API with historical Coinbase and Binance listing announcement timestamps so we can test listing momentum and post-listing reversal.",
        source_markets_json='["crypto"]',
        source_topics_json='["data", "exchange_listings"]',
        expected_types={"data_source", "research_question"},
        expected_markets={"crypto"},
        expected_required_data={"historical_prices"},
        expected_routes={"data_collection_loop"},
    ),
    EvalCase(
        case_id="thirteen_f_filing_question",
        title="Do 13F filings reveal ETF positioning trades?",
        text="Research whether changes in 13F filings around BTC ETFs can identify delta-neutral positioning or delayed market reactions.",
        source_markets_json='["stocks", "crypto"]',
        source_topics_json='["filings"]',
        expected_types={"research_question", "market_observation"},
        expected_markets={"stocks", "crypto"},
        expected_required_data={"sec_filings"},
        expected_routes={"data_collection_loop", "human_review_loop"},
    ),
    EvalCase(
        case_id="small_cap_earnings_momentum",
        title="Small-cap earnings volume momentum",
        text="Test whether small-cap stocks with positive earnings surprises and abnormal volume continue momentum for 3 to 10 trading days.",
        source_markets_json='["stocks"]',
        source_topics_json='["earnings", "momentum"]',
        expected_types={"strategy_idea"},
        expected_markets={"stocks"},
        expected_required_data={"earnings_calendar", "price_volume"},
        expected_routes={"backtest_loop", "data_collection_loop"},
    ),
]


def run_extractor_eval(settings: Settings) -> tuple[int, list[str]]:
    extractor = _extractor(settings)
    lines = [f"extractor={settings.extractor_provider}", f"cases={len(EVAL_CASES)}"]
    total = 0
    possible = len(EVAL_CASES) * 10
    for case in EVAL_CASES:
        result = extractor.extract(_row_for_case(case))
        score, notes = _score_case(case, result)
        total += score
        produced = ", ".join(record.record_type for record in result.records) or "none"
        lines.append(f"{case.case_id}: {score}/10 | produced={produced} | {'; '.join(notes)}")
    percent = round((total / possible) * 100)
    lines.insert(2, f"score={total}/{possible} ({percent}%)")
    return percent, lines


def _row_for_case(case: EvalCase) -> sqlite3.Row:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE raw (
            source_id TEXT,
            source_type TEXT,
            url TEXT,
            title TEXT,
            text TEXT,
            source_markets_json TEXT,
            source_topics_json TEXT
        )
        """
    )
    connection.execute(
        "INSERT INTO raw VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "eval",
            "manual",
            f"manual://eval/{case.case_id}",
            case.title,
            case.text,
            case.source_markets_json,
            case.source_topics_json,
        ),
    )
    return connection.execute("SELECT * FROM raw").fetchone()


def _score_case(case: EvalCase, result: ExtractionResult) -> tuple[int, list[str]]:
    notes: list[str] = []
    records = result.records
    if not records:
        return 0, ["no records"]

    produced_types = {record.record_type for record in records}
    produced_markets = {market for record in records for market in record.markets}
    produced_required_data = {item for record in records for item in record.required_data}
    produced_routes = {route for record in records for route in record.next_loop_targets}

    score = 2
    if produced_types & case.expected_types:
        score += 3
        notes.append("type ok")
    else:
        notes.append(f"type miss expected={sorted(case.expected_types)}")

    if not case.expected_markets or produced_markets & case.expected_markets:
        score += 2
        notes.append("market ok")
    else:
        notes.append(f"market miss expected={sorted(case.expected_markets)}")

    if not case.expected_required_data or produced_required_data & case.expected_required_data:
        score += 2
        notes.append("data ok")
    else:
        notes.append(f"data miss expected={sorted(case.expected_required_data)}")

    if not case.expected_routes or produced_routes & case.expected_routes:
        score += 1
        notes.append("route ok")
    else:
        notes.append(f"route miss expected={sorted(case.expected_routes)}")

    return min(score, 10), notes
