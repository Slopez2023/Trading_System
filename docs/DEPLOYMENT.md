# Deployment

This is the deployment plan for the research loop. The target for `v0.3.0` is a clean 24/7 terminal-first service that can feed later loops.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
cp .env.example .env
```

Recommended `.env` for low-cost AI extraction:

```env
RESEARCH_LOOP_EXTRACTOR=hybrid
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=deepseek/deepseek-v4-flash
RESEARCH_LOOP_MAX_OUTPUT_TOKENS=1200
RESEARCH_LOOP_DB_PATH=data/research_loop.sqlite3
RESEARCH_LOOP_DIGEST_DIR=digests
RESEARCH_LOOP_LOG_PATH=logs/research_loop.jsonl
```

## First Run

```bash
python3 -m research_loop init-db
python3 -m research_loop sources import --file loops/research_loop/sources.json
python3 -m research_loop smoke-test
python3 -m research_loop monitor --once
```

Expected result:

```text
raw_items_processed=1
records_created=1
monitor shows at least 1 research record
```

## Run Modes

One cycle:

```bash
python3 -m research_loop run-once
```

Continuous loop:

```bash
python3 -m research_loop loop --sleep-seconds 900
```

Live monitor in another terminal:

```bash
python3 -m research_loop monitor
```

## Pre-Deployment Checks

Run these before leaving the loop running:

```bash
python3 -m pytest
python3 -m compileall research_loop tests
python3 -m research_loop smoke-test
python3 -m research_loop sources health
python3 -m research_loop records export --file /tmp/research_records.json --limit 25
python3 -m research_loop monitor --once
```

## Runtime Files

These are local runtime files and should not be committed:

```text
.env
data/research_loop.sqlite3
data/research_loop.sqlite3-wal
data/research_loop.sqlite3-shm
digests/*.md
logs/*.jsonl
```

## v0.3.0 Deployment Gaps

Before calling this deployment-ready:

- [x] Add structured logs.
- [x] Add source config import/export.
- [ ] Add database backup instructions.
- [ ] Add a restart wrapper using launchd, systemd, tmux, or supervisor.
- [ ] Add a production release checklist.
- [ ] Add source packs so a clean install has useful real sources.

## Operating Rule

Run the research loop as an inbox, not as a trading system. Later loops must validate, backtest, and risk-check records before any trading automation exists.
