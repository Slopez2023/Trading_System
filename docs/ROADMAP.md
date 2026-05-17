# Roadmap

This project is a loop-based trading research system. The current goal is to finish the research loop through `v0.3.0`, then use its output as input for the next loops.

## v0.1.0 - Foundation

Status: complete.

- [x] SQLite database
- [x] Source registry
- [x] Raw item storage
- [x] Research record storage
- [x] Evidence links
- [x] RSS collector
- [x] Reddit JSON collector
- [x] Local extractor
- [x] CLI commands
- [x] Manual raw input
- [x] Markdown digest
- [x] Tests and GitHub Actions

## v0.2.0 - Working AI Research Loop

Status: complete.

- [x] Add extractor provider setting: `local`, `openai`, `hybrid`
- [x] Add OpenRouter/OpenAI-compatible AI extraction
- [x] Keep local extractor as fallback
- [x] Add `.env` loading
- [x] Support `OPENROUTER_API_KEY`
- [x] Set low-cost OpenRouter default: `deepseek/deepseek-v4-flash`
- [x] Add source scheduling
- [x] Add source/raw management commands
- [x] Add source error tracking
- [x] Add raw item processing states
- [x] Add smoke test command
- [x] Add extractor benchmark command
- [x] Add live terminal monitor
- [x] Add archive and reprocess commands
- [x] Normalize extracted records before saving
- [x] Add conservative duplicate merging with evidence preservation
- [x] Add tests for extraction, scheduling, monitoring, normalization, and dedupe

Acceptance:

- [x] Local extraction works without API keys
- [x] AI extraction works through OpenRouter configuration
- [x] Hybrid mode falls back to local extraction
- [x] CLI can be watched live with `monitor`
- [x] Duplicate obvious ideas merge without losing source evidence

## v0.3.0 - Deployment-Ready Research Loop

Status: next.

Purpose: make the research loop clean enough to run 24/7 while other loops are built around it.

### Repo and Loop Structure

- [x] Add `loops/` folder as the system home for loop docs
- [x] Add research loop contract docs
- [ ] Add a starter folder for the next loop once its responsibility is chosen
- [ ] Add a top-level system flow diagram after the second loop is named

### Source Management

- [ ] Add `sources.yaml`
- [ ] Add source import command
- [ ] Add source export command
- [ ] Add source validation before activation
- [ ] Add source categories: `social`, `news`, `exchange`, `research`, `market_data`, `filing`
- [ ] Add first exchange announcement source pack
- [ ] Add first market/news RSS source pack
- [ ] Add source candidate approval workflow

### Deployment Readiness

- [x] Document local `.env` setup
- [x] Document monitor and smoke-test commands
- [ ] Add structured logging
- [ ] Add deployment runbook for local Mac/server
- [ ] Add restart recommendation: launchd, systemd, tmux, or supervisor
- [ ] Add database backup instructions
- [ ] Add production smoke checklist
- [ ] Add versioned release checklist

### Output Quality

- [x] Normalize statuses, markets, risks, scores, and loop targets
- [x] Preserve weird/early ideas instead of filtering hard
- [x] Merge obvious duplicates conservatively
- [ ] Add record export command for downstream loops
- [ ] Add source-quality summary command
- [ ] Add daily digest command with stable naming

### Acceptance for v0.3.0

- [ ] A fresh clone can be configured from `.env.example`
- [ ] `smoke-test` passes on a clean database
- [ ] `loop` can run continuously with documented monitoring
- [ ] Sources can be managed without editing Python code
- [ ] Downstream loops have a documented input contract
- [ ] Tests and compile checks pass before release

## After v0.3.0

- Validation loop: decide what should be backtested, researched more, ignored, or watched.
- Backtest loop: convert selected strategy ideas into test specs and results.
- Data loop: collect required market data for selected records.
- Review loop: human approval and audit trail.
- Execution loop: only after validation, backtesting, and risk controls exist.
