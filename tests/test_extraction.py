from __future__ import annotations

import sqlite3

from research_loop.extraction import LocalResearchExtractor


def test_local_extractor_creates_strategy_record() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE raw (
            title TEXT,
            text TEXT,
            source_markets_json TEXT,
            source_topics_json TEXT
        )
        """
    )
    connection.execute(
        """
        INSERT INTO raw VALUES (?, ?, ?, ?)
        """,
        (
            "Funding rate mean reversion idea",
            "Backtest whether BTC perps fade after funding rate and open interest spikes with high volume.",
            '["crypto"]',
            '["quant"]',
        ),
    )
    row = connection.execute("SELECT * FROM raw").fetchone()

    result = LocalResearchExtractor().extract(row)

    assert result.relevance_score > 0.25
    assert result.records
    assert result.records[0].record_type == "strategy_idea"
    assert "funding_rates" in result.records[0].required_data
    assert "backtest_loop" in result.records[0].next_loop_targets
