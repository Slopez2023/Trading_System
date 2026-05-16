from __future__ import annotations

import sqlite3

from research_loop.config import Settings
from research_loop.openai_extraction import OpenAIResearchExtractor


def _raw_row() -> sqlite3.Row:
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
        """
        INSERT INTO raw VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "manual",
            "manual",
            "",
            "BTC funding spike reversal",
            "Backtest whether BTC perps reverse after funding and open interest spike. Watch slippage.",
            '["crypto"]',
            '["manual"]',
        ),
    )
    return connection.execute("SELECT * FROM raw").fetchone()


def test_openai_extractor_parses_structured_response() -> None:
    def fake_post(url, payload, headers, timeout_seconds):
        assert url.endswith("/responses")
        assert payload["text"]["format"]["type"] == "json_schema"
        assert headers["Authorization"] == "Bearer test-key"
        return {
            "output_text": """
            {
              "relevance_score": 0.91,
              "records": [
                {
                  "record_type": "strategy_idea",
                  "title": "Fade BTC funding and open interest spikes",
                  "summary": "Test whether crowded BTC perpetual positioning reverses after funding and open interest spike.",
                  "details": "Backtest BTC perpetual futures after funding and open interest spike.",
                  "markets": ["crypto"],
                  "assets": ["BTC"],
                  "timeframes": ["intraday", "1D"],
                  "tags": ["funding", "open_interest", "mean_reversion"],
                  "required_data": ["funding_rates", "open_interest", "price_volume"],
                  "risks": ["slippage may erase edge"],
                  "scores": {
                    "priority": 86,
                    "novelty": 55,
                    "testability": 90,
                    "data_availability": 80,
                    "urgency": 60,
                    "confidence": 68,
                    "source_quality": 50
                  },
                  "next_loop_targets": ["data_collection_loop", "backtest_loop"],
                  "evidence_summary": "The source proposes backtesting BTC reversals after funding and open interest spikes.",
                  "evidence_relationship": "source_observation"
                }
              ]
            }
            """
        }

    settings = Settings(openai_api_key="test-key")
    result = OpenAIResearchExtractor(settings, http_post=fake_post).extract(_raw_row())

    assert result.relevance_score == 0.91
    assert len(result.records) == 1
    assert result.records[0].record_type == "strategy_idea"
    assert "backtest_loop" in result.records[0].next_loop_targets


def test_openrouter_extractor_uses_chat_completions() -> None:
    def fake_post(url, payload, headers, timeout_seconds):
        assert url == "https://openrouter.ai/api/v1/chat/completions"
        assert payload["model"] == "qwen/qwen3-30b-a3b-instruct-2507"
        assert payload["max_tokens"] == 1200
        assert payload["response_format"]["type"] == "json_schema"
        return {
            "choices": [
                {
                    "message": {
                        "content": """
                        {
                          "relevance_score": 0.75,
                          "records": [
                            {
                              "record_type": "strategy_idea",
                              "title": "Fade BTC funding spikes",
                              "summary": "Test whether BTC reverses after funding spikes.",
                              "details": "Backtest BTC reversals after funding spikes.",
                              "markets": ["crypto"],
                              "assets": ["BTC"],
                              "timeframes": ["1D"],
                              "tags": ["funding"],
                              "required_data": ["funding_rates", "price_volume"],
                              "risks": ["slippage"],
                              "scores": {
                                "priority": 70,
                                "novelty": 40,
                                "testability": 85,
                                "data_availability": 80,
                                "urgency": 50,
                                "confidence": 60,
                                "source_quality": 50
                              },
                              "next_loop_targets": ["backtest_loop"],
                              "evidence_summary": "Source mentions backtesting BTC reversals after funding spikes.",
                              "evidence_relationship": "source_observation"
                            }
                          ]
                        }
                        """
                    }
                }
            ]
        }

    settings = Settings(
        openai_api_key="test-key",
        openai_base_url="https://openrouter.ai/api/v1",
        openai_model="qwen/qwen3-30b-a3b-instruct-2507",
    )
    result = OpenAIResearchExtractor(settings, http_post=fake_post).extract(_raw_row())

    assert result.records[0].title == "Fade BTC funding spikes"
