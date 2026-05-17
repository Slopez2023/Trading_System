# Loop Contracts

This repo is designed as multiple loops that feed each other. Each loop should document what it reads, what it writes, and what other loops can rely on.

## Research Loop Contract

The research loop captures source-backed ideas and writes structured records.

Input:

- Configured sources
- Manual raw items
- RSS feeds
- Reddit JSON feeds
- Future exchange/news/market-data sources

Output:

- `research_records`
- `evidence_links`
- `raw_items`
- Markdown digests

Primary downstream table:

```text
research_records
```

Important fields:

- `record_type`: kind of record, such as `strategy_idea`, `risk_warning`, `market_theme`, or `research_question`
- `title`: short human-readable name
- `summary`: concise explanation
- `details`: deeper notes
- `markets_json`: markets involved
- `assets_json`: assets involved
- `required_data_json`: data needed by validation/backtest loops
- `risks_json`: visible risks
- `scores_json`: priority, novelty, testability, urgency, confidence
- `status`: soft state such as `needs_data`, `ready_for_backtest`, or `weird_but_interesting`
- `next_loop_targets_json`: suggested downstream loops
- `fingerprint`: conservative duplicate key

Evidence table:

```text
evidence_links
```

Use this to know which raw source items support a record.

Raw source table:

```text
raw_items
```

Use this only when another loop needs original evidence text or URLs.

## Rules for Future Loops

- Read structured records first.
- Follow evidence links when the source matters.
- Do not mutate raw evidence.
- Do not treat AI extraction as truth.
- Do not trade from a research record directly.
- Write your own output table or export format.

## Suggested Next Loop

The next loop should probably be a validation loop.

Purpose:

```text
Research record -> validation decision -> data/backtest task
```

It should answer:

- Is this clear enough to test?
- What exact data is needed?
- What hypothesis should be tested?
- What would invalidate the idea?
- Should this go to backtesting, more research, watchlist, or archive?

## Experiment Planner Loop Contract

The experiment planner loop turns selected research records into strict experiment specs.

Input:

- `research_records`
- `evidence_links` when source context is needed

Output:

- `experiment_specs`
- `experiment_data_requirements`

Primary downstream table:

```text
experiment_specs
```

Important fields:

- `source_record_id`: source research record
- `thesis`: testable claim
- `experiment_type`: `signal_backtest`, `event_study`, or `risk_model`
- `market` and `asset`
- `timeframes_json`
- `data_needed_json`
- `entry_rule`
- `exit_rule`
- `cost_model_json`
- `success_metric`
- `reject_if`
- `status`
- `scores_json`: ROI/testability routing scores

Rules:

- The planner writes specs, not backtest code.
- Backtests should consume specs through templates.
- Data loops should consume `experiment_data_requirements`.

## Data Loop Contract

The data loop turns experiment requirements into local market datasets.

Input:

- `experiment_data_requirements`
- `experiment_specs`

Output:

- `data_jobs`
- `market_datasets`
- local CSV files under `data/market/`

Primary downstream table:

```text
market_datasets
```

Important fields:

- `experiment_id`: experiment spec the data belongs to
- `dataset_type`: `ohlcv`, `volume`, `funding_rates`, or `open_interest`
- `provider`: initial MVP uses `binance_usdm`
- `symbol`: initial MVP supports `BTCUSDT`
- `timeframe`
- `path`
- `row_count`
- `start_at` / `end_at`
- `status`

Rules:

- Data collection marks source requirements `available` only after a dataset is written.
- The MVP is BTC/Binance-only until strategy and backtest loops prove the path.
