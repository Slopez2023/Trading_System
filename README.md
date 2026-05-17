# Trading System

Version: `0.1.0`

This repo is being built as a multi-loop trading research system. The first working loop is the research loop.

The research loop's job is narrow:

```text
Sources -> raw saved evidence -> extracted research records -> digest / downstream queues
```

It does not trade, place orders, or build bots. It creates a source-backed research inbox that other loops can consume later.

## Repo Shape

```text
loops/
  research_loop/        loop docs, contract, deployment notes
research_loop/          Python package for the research loop CLI
tests/                  automated tests
docs/                   system docs and roadmap
prompts/                AI extraction prompt intent
data/                   ignored local SQLite runtime files
digests/                ignored local Markdown digest output
```

Future loops should get their own folder under `loops/`, then consume the research loop through the documented database/export contract instead of reaching into random internals.

## What v0.1.0 Includes

- SQLite storage for sources, raw items, research records, evidence links, and source performance.
- A source registry so the system remembers where to look.
- RSS and Reddit JSON collectors.
- Raw item deduplication by URL and content hash.
- A deterministic local extractor that creates useful records without an API key.
- Optional OpenRouter/OpenAI-compatible extractor for AI-backed research extraction.
- Hybrid extractor mode that uses AI with local fallback.
- Record normalization and conservative duplicate merging.
- Terminal monitor for live CLI visibility.
- A Markdown digest generator.
- CLI commands for init, seed, collect, extract, monitor, archive, reprocess, and run-once.

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

Use AI extraction:

```bash
cp .env.example .env
# edit .env and set OPENROUTER_API_KEY
python3 -m research_loop run-once
```

OpenRouter example in `.env`:

```env
RESEARCH_LOOP_EXTRACTOR=hybrid
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=deepseek/deepseek-v4-flash
RESEARCH_LOOP_MAX_OUTPUT_TOKENS=1200
```

Free OpenRouter option, if available:

```env
OPENAI_MODEL=deepseek/deepseek-v4-flash:free
```

Or pass a model directly:

```bash
python3 -m research_loop --extractor hybrid --openai-model deepseek/deepseek-v4-flash extract-once
```

This app supports OpenRouter through `OPENROUTER_API_KEY`. It does not read Codex's private login/session files.

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
python3 -m research_loop sources list
python3 -m research_loop sources validate --file loops/research_loop/sources.json
python3 -m research_loop sources import --file loops/research_loop/sources.json
python3 -m research_loop sources export --file /tmp/sources.json
python3 -m research_loop raw list --status pending
python3 -m research_loop smoke-test
python3 -m research_loop eval-extractor
python3 -m research_loop monitor
python3 -m research_loop monitor --once
python3 -m research_loop records archive --yes
python3 -m research_loop records repair-quality
python3 -m research_loop records export --file /tmp/research_records.json --limit 100
python3 -m research_loop reprocess --status extracted --limit 25
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

Extracted records are normalized before saving. The normalizer fixes structure without hard-filtering unusual ideas:

```text
allowed loop targets
soft statuses
market cleanup
data/risk cleanup
score bounds
fingerprint repair
```

More detail:

- [Vision](docs/VISION.md)
- [Architecture](docs/architecture.md)
- [Loop contracts](docs/LOOP_CONTRACTS.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Roadmap](docs/ROADMAP.md)
- [Project checklist](docs/CHECKLIST.md)

## Development

```bash
python3 -m pytest
python3 -m compileall research_loop tests
```

Contribution rules are in [CONTRIBUTING.md](CONTRIBUTING.md).

Runtime files are ignored by git:

```text
data/*.sqlite3
digests/*.md
logs/*.jsonl
.env
```

## v0.3.0 Finish Line

The next target is making this loop deployment-ready so the rest of the system can build on top of it:

- JSON source config file and import/export commands.
- Better source packs for exchange, news, Reddit, and RSS feeds.
- Structured logs and a simple 24/7 runbook.
- Stable downstream output contract.
- Deployment checklist for local Mac or server use.

## Safety Boundary

This project is a research ingestion system. It does not provide financial advice, does not execute trades, and does not decide whether a strategy is profitable. Downstream systems must validate, backtest, and risk-check anything this loop captures.
