# Trading Research Loop

Version: `0.1.0`

This is the first version of the 24/7 research ingestion loop.

Its job is narrow:

```text
Sources -> raw saved evidence -> extracted research records -> digest / downstream queues
```

It does not trade, place orders, or build bots. It creates a source-backed research inbox that other loops can consume later.

## What v0.1.0 Includes

- SQLite storage for sources, raw items, research records, evidence links, and source performance.
- A source registry so the system remembers where to look.
- RSS and Reddit JSON collectors.
- Raw item deduplication by URL and content hash.
- A deterministic local extractor that creates useful records without an API key.
- A Markdown digest generator.
- CLI commands for init, seed, collect, extract, and run-once.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m research_loop init-db
python3 -m research_loop seed-sources
python3 -m research_loop run-once
python3 -m research_loop digest
python3 -m research_loop stats
```

The default database is:

```text
data/research_loop.sqlite3
```

Digests are written to:

```text
digests/
```

## Commands

```bash
python3 -m research_loop init-db
python3 -m research_loop seed-sources
python3 -m research_loop collect-once
python3 -m research_loop extract-once
python3 -m research_loop run-once
python3 -m research_loop digest
python3 -m research_loop list-records
python3 -m research_loop add-raw --title "Funding spike idea" --text "Backtest whether BTC reverses after funding and open interest spike."
python3 -m research_loop stats
python3 -m research_loop loop --sleep-seconds 900
```

Use a custom database:

```bash
python3 -m research_loop --db /path/to/research.sqlite3 run-once
```

## Design

The loop stores the original source item first, then extraction creates one or more structured records:

```text
strategy_idea
market_observation
market_theme
anomaly
risk_warning
data_source
research_question
asset_watchlist
event_catalyst
source_candidate
contradiction
```

Every research record links back to raw evidence.

More detail is in [docs/architecture.md](docs/architecture.md).

## Development

```bash
python3 -m pytest
python3 -m compileall research_loop tests
```

Runtime files are ignored by git:

```text
data/*.sqlite3
digests/*.md
.env
```

## Next Versions

Likely next steps:

- Add OpenAI extraction provider behind the same extractor interface.
- Add X, exchange announcements, SEC filings, and market-data anomaly collectors.
- Add semantic dedupe/merge for similar research records.
- Add source performance scoring based on downstream outcomes.
- Add a dashboard or API for other loops.
