# Roadmap

This roadmap turns the research loop into a reliable 24/7 research ingestion system.

The guiding rule is:

```text
Do not add trading execution here.
This repo captures, structures, scores, dedupes, and routes research records.
```

## Release Strategy

Each version should have a narrow purpose:

- `v0.1.x`: harden the foundation already built.
- `v0.2.x`: add real AI extraction safely.
- `v0.3.x`: make source management reliable.
- `v0.4.x`: expand source coverage.
- `v0.5.x`: dedupe, merge, and route records.
- `v0.6.x`: make it operable as a 24/7 service.
- `v0.7.x`: expose output to other loops.
- `v0.8.x`: add review workflow and dashboard/API ergonomics.
- `v1.0.0`: stable production research inbox.

## v0.1.0 - Foundation

Status: complete.

Purpose: prove the basic ingestion shape.

Checklist:

- [x] SQLite database
- [x] Source registry
- [x] Raw item storage
- [x] Research record storage
- [x] Evidence links
- [x] Source performance table
- [x] RSS collector
- [x] Reddit JSON collector
- [x] Local deterministic extractor
- [x] CLI commands
- [x] Manual raw item input
- [x] Markdown digest
- [x] Unit tests
- [x] GitHub Actions
- [x] Project docs
- [x] GitHub issue/PR templates

Acceptance:

- [x] `python3 -m pytest` passes
- [x] `python3 -m compileall research_loop tests` passes
- [x] `init-db -> add-raw -> extract-once -> list-records` works

## v0.1.1 - Hardening Pass

Purpose: make the current non-AI system safer and less misleading.

Why this comes next: the core works, but classification, scheduling, and failure tracking are not strong enough for long-running use.

Checklist:

- [ ] Fix classifier precedence so strategy intent is not overwritten by risk terms
- [ ] Allow one raw item to produce multiple primary records, such as `strategy_idea` plus `risk_warning`
- [ ] Respect `check_frequency_minutes` and `last_checked_at`
- [ ] Add source due/not-due logic
- [ ] Add raw item processing states: `pending`, `processing`, `extracted`, `ignored`, `failed`
- [ ] Add processing claim step to avoid duplicate processing if two loops run
- [ ] Store collector errors in the database
- [ ] Add failure count and last error fields for sources
- [ ] Replace core `print()` calls with structured logging
- [ ] Add CLI command: `sources list`
- [ ] Add CLI command: `sources enable`
- [ ] Add CLI command: `sources disable`
- [ ] Add CLI command: `raw list --status pending`
- [ ] Add integration test for manual item workflow
- [ ] Add collector tests using static Reddit/RSS fixtures
- [ ] Add tests for schedule/due source behavior
- [ ] Add tests for risk-plus-strategy extraction behavior

Acceptance:

- [ ] Running `loop` does not fetch sources before they are due
- [ ] Collection failures are visible from a CLI command
- [ ] A strategy text containing risk words still creates a `strategy_idea`
- [ ] Two extractor runs cannot process the same raw item at the same time
- [ ] Tests cover CLI smoke flow and collector parsing

## v0.1.2 - Repo and Release Hygiene

Purpose: make the repository easier to maintain before larger features.

Checklist:

- [ ] Choose and add license
- [ ] Add `Makefile` or task runner commands
- [ ] Add `ruff` for linting
- [ ] Add type checking plan, likely `mypy` or `pyright`
- [ ] Add CI matrix for Python 3.11 and 3.12
- [ ] Add release checklist doc
- [ ] Add changelog discipline for each version
- [ ] Add issue labels recommendation
- [ ] Add branch protection recommendation
- [ ] Add `.editorconfig`

Acceptance:

- [ ] One command runs local checks
- [ ] CI runs tests, compile check, and lint
- [ ] Public repo has clear license and contribution rules

## v0.2.0 - Real AI Extraction

Purpose: add LLM-backed analysis while keeping local extraction as fallback.

Checklist:

- [ ] Add extractor interface/protocol
- [ ] Keep `LocalResearchExtractor` as fallback
- [ ] Add OpenAI extractor implementation
- [ ] Add provider setting: `local`, `openai`, `hybrid`
- [ ] Read provider config from environment/config file
- [ ] Define strict JSON schema for extracted records
- [ ] Validate model outputs before database writes
- [ ] Add retry handling for malformed model output
- [ ] Add model timeout handling
- [ ] Add token/cost logging fields
- [ ] Add prompt version tracking
- [ ] Store extractor name and version on research records
- [ ] Add model response fixture tests
- [ ] Add tests for invalid JSON response handling
- [ ] Add tests for fallback from AI extractor to local extractor

Acceptance:

- [ ] AI extraction can be enabled without changing collectors/storage
- [ ] Invalid model output does not corrupt the database
- [ ] Every AI-created record links back to raw evidence
- [ ] Local extractor still works with no API key

## v0.2.1 - AI Quality Controls

Purpose: reduce hallucinations and make model output auditable.

Checklist:

- [ ] Add extraction prompt IDs and versions
- [ ] Save prompt version used per extraction
- [ ] Add source quote/evidence requirement for model-created records
- [ ] Add confidence reason field
- [ ] Add uncertainty notes field
- [ ] Add model refusal/skip path for low-value content
- [ ] Add record quality tests using curated examples
- [ ] Add evaluation set with expected record types
- [ ] Add command: `eval-extractor`

Acceptance:

- [ ] Extractor quality can be tested against fixed examples
- [ ] Model-created records include evidence summaries
- [ ] Low-quality raw items are ignored cleanly

## v0.3.0 - Source Management

Purpose: make sources first-class, inspectable, and easy to adjust.

Checklist:

- [ ] Add `sources.yaml`
- [ ] Add source import command
- [ ] Add source export command
- [ ] Add source validation
- [ ] Add source categories: social, news, exchange, research, market_data, filing
- [ ] Add source priority
- [ ] Add source tags
- [ ] Add source candidate table or record type workflow
- [ ] Add command: `sources add`
- [ ] Add command: `sources update`
- [ ] Add command: `sources health`
- [ ] Add source performance rollup
- [ ] Add source score calculation
- [ ] Track items collected per source
- [ ] Track records created per source
- [ ] Track promoted/rejected records per source

Acceptance:

- [ ] Sources can be edited without code changes
- [ ] No source is collected if disabled
- [ ] Source quality can be viewed from CLI
- [ ] Source candidates can be reviewed before activation

## v0.3.1 - Source Discovery

Purpose: let the system discover possible new sources without blindly trusting them.

Checklist:

- [ ] Extract source candidates from raw item links
- [ ] Track cited domains/authors
- [ ] Add source candidate status: `candidate`, `approved`, `rejected`, `active`
- [ ] Add command: `sources candidates`
- [ ] Add command: `sources approve-candidate`
- [ ] Add command: `sources reject-candidate`
- [ ] Add source candidate reason field
- [ ] Add source candidate evidence links

Acceptance:

- [ ] New source candidates are stored separately from active sources
- [ ] A candidate cannot become active without explicit approval

## v0.4.0 - Collector Expansion

Purpose: expand beyond Reddit/RSS while preserving the collector contract.

Checklist:

- [ ] Add exchange announcement collector
- [ ] Add Binance announcements source
- [ ] Add Coinbase announcements source
- [ ] Add Kraken announcements source
- [ ] Add SEC filing collector
- [ ] Add economic calendar collector
- [ ] Add market news RSS bundle
- [ ] Add crypto funding rate collector
- [ ] Add open interest collector
- [ ] Add liquidation data collector if source is available
- [ ] Add market-data anomaly collector interface
- [ ] Add source-specific rate limit handling
- [ ] Add collector fixture tests for each collector

Acceptance:

- [ ] Every collector returns normalized `RawItem` records
- [ ] Collector failures are isolated by source
- [ ] Rate limits are respected
- [ ] Tests do not require live network access

## v0.4.1 - X / Social Decision

Purpose: decide how to handle X and other social sources responsibly.

Checklist:

- [ ] Document X API options and limits
- [ ] Decide whether to support X API, external export, or manual import
- [ ] Add social post raw item shape
- [ ] Add author/source reputation fields
- [ ] Add engagement metadata fields
- [ ] Add duplicate repost handling
- [ ] Add policy notes for terms-of-service compliance

Acceptance:

- [ ] Social ingestion path is legally/API clear
- [ ] X support is either implemented or explicitly deferred

## v0.5.0 - Dedupe, Merge, and Memory

Purpose: stop the research inbox from becoming a pile of duplicates.

Checklist:

- [ ] Add exact dedupe normalization for records
- [ ] Add semantic similarity interface
- [ ] Add embeddings provider abstraction
- [ ] Add local text similarity fallback
- [ ] Add duplicate candidate table
- [ ] Add merge command
- [ ] Add auto-merge threshold
- [ ] Add manual-review threshold
- [ ] Merge evidence links into existing records
- [ ] Preserve record history when merged
- [ ] Add canonical record concept
- [ ] Add tests for duplicate strategy wording

Acceptance:

- [ ] Similar ideas from multiple sources become one stronger record
- [ ] Evidence is appended instead of lost
- [ ] Auto-merge behavior is tested and configurable

## v0.5.1 - Record Lifecycle and Routing

Purpose: make records useful to downstream loops.

Checklist:

- [ ] Add record statuses: `captured`, `needs_review`, `ready_for_backtest`, `needs_data`, `rejected`, `archived`
- [ ] Add status transition rules
- [ ] Add routing queue table
- [ ] Add next-loop target validation
- [ ] Add route command
- [ ] Add export command for downstream loops
- [ ] Add backtest-loop handoff schema
- [ ] Add data-collection-loop handoff schema
- [ ] Add risk-review-loop handoff schema
- [ ] Add route history

Acceptance:

- [ ] Downstream loops can consume records by status/target
- [ ] Routing changes are auditable
- [ ] Invalid route targets are rejected

## v0.6.0 - 24/7 Service Readiness

Purpose: run reliably without babysitting.

Checklist:

- [ ] Add service mode separate from simple CLI loop
- [ ] Add graceful shutdown
- [ ] Add lock file or process guard
- [ ] Add structured logs
- [ ] Add log rotation guidance
- [ ] Add heartbeat table
- [ ] Add health command
- [ ] Add retry/backoff behavior
- [ ] Add dead-letter handling for failed raw items
- [ ] Add backup command
- [ ] Add database vacuum/maintenance command
- [ ] Add deployment docs for local Mac launchd
- [ ] Add deployment docs for Docker

Acceptance:

- [ ] Service can stop cleanly
- [ ] Failures are visible from CLI
- [ ] A single machine cannot accidentally run duplicate service workers without warning
- [ ] Database backup path is documented and tested

## v0.6.1 - Observability

Purpose: know what the loop is doing.

Checklist:

- [ ] Add metrics counters
- [ ] Track source fetch duration
- [ ] Track extractor duration
- [ ] Track model cost if AI enabled
- [ ] Track records created per hour/day
- [ ] Track ignored raw item rate
- [ ] Track failure rate per source
- [ ] Add command: `metrics`
- [ ] Add daily summary report

Acceptance:

- [ ] User can answer: what did it collect, what failed, what did it create, and what cost did it incur

## v0.7.0 - API and Exports

Purpose: make this repo useful to the rest of the trading system.

Checklist:

- [ ] Add JSON export command
- [ ] Add CSV export command
- [ ] Add stable downstream schema docs
- [ ] Add lightweight HTTP API
- [ ] Add endpoint for research records
- [ ] Add endpoint for raw item evidence
- [ ] Add endpoint for source status
- [ ] Add endpoint for routing queues
- [ ] Add API tests
- [ ] Add read-only mode for API

Acceptance:

- [ ] Other loops can pull records without reading SQLite directly
- [ ] Export schema is versioned
- [ ] API cannot mutate data unless explicitly enabled

## v0.8.0 - Review Workflow

Purpose: let a human review, promote, reject, and annotate records.

Checklist:

- [ ] Add review commands
- [ ] Add record notes
- [ ] Add reviewer field
- [ ] Add promote/reject commands
- [ ] Add digest sections by status
- [ ] Add daily top-records digest
- [ ] Add evidence display command
- [ ] Add contradiction display command
- [ ] Add simple dashboard decision: terminal UI, web UI, or external app

Acceptance:

- [ ] User can review records without touching SQLite manually
- [ ] Promotions/rejections update source performance
- [ ] Digest is useful for daily review

## v0.9.0 - Production Polish

Purpose: close gaps before v1.

Checklist:

- [ ] Documentation pass
- [ ] Configuration pass
- [ ] Security pass
- [ ] Performance pass
- [ ] Database migration pass
- [ ] Collector reliability pass
- [ ] AI extraction quality pass
- [ ] End-to-end test suite
- [ ] Load test with large raw item volume
- [ ] Backup/restore test
- [ ] Upgrade test from older DB version
- [ ] Public/private repo readiness review

Acceptance:

- [ ] System can run for several days without manual database repair
- [ ] Common failure modes are handled
- [ ] Upgrade path is documented

## v1.0.0 - Stable Research Inbox

Purpose: a dependable 24/7 research ingestion system for downstream trading research loops.

Checklist:

- [ ] Stable database schema or migration path
- [ ] Reliable source scheduling
- [ ] Source health and performance scoring
- [ ] AI-backed extraction with fallback
- [ ] Record dedupe and merge
- [ ] Evidence-linked research records
- [ ] Downstream queue/export/API
- [ ] Review workflow
- [ ] Service deployment docs
- [ ] Backup and restore docs
- [ ] Operational metrics
- [ ] Full test suite
- [ ] Security and API-key handling docs

Acceptance:

- [ ] Can run 24/7 locally or on a server
- [ ] Can recover from collector/API failures
- [ ] Can export usable research records to downstream loops
- [ ] Does not execute trades
- [ ] Every record is auditable back to source evidence

## Backlog Ideas

These are useful but should not distract from the main sequence.

- [ ] Web dashboard
- [ ] Browser extension for manually saving sources
- [ ] Discord/Slack digest delivery
- [ ] Vector database support
- [ ] Postgres backend
- [ ] Multi-user review workflow
- [ ] Source-specific prompt tuning
- [ ] Auto-generated backtest specs
- [ ] Integration with later bot-building loops
- [ ] Data vendor adapters
