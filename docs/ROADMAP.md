# Roadmap

## v0.1.0 - Current

Foundation release.

- SQLite schema
- Source registry
- Raw item storage
- Research record storage
- Evidence links
- RSS collector
- Reddit JSON collector
- Local rule-based extractor
- CLI commands
- Markdown digest
- Tests and GitHub Actions

## v0.2.0 - Real AI Extraction

Primary goal: replace the weak local analyzer with a proper LLM-backed extractor while keeping the local extractor as fallback.

- Add extractor interface
- Add OpenAI extractor implementation
- Add JSON schema validation for model outputs
- Add retry and malformed-output handling
- Add config/env support for provider selection
- Add tests with mocked model responses
- Preserve source links in every model-generated record

## v0.3.0 - Better Source Management

Primary goal: make sources easier to add, review, and score.

- Add `sources.yaml` import/export
- Add source candidate records
- Add source performance scoring
- Add collection frequency logic
- Add source enable/disable commands
- Add source health checks

## v0.4.0 - More Collectors

Primary goal: expand source coverage.

- Exchange announcements
- SEC filings
- Economic calendar
- Market news RSS bundle
- Crypto funding/open-interest source adapter
- Optional X integration, depending on API access

## v0.5.0 - Dedupe and Routing

Primary goal: reduce duplicate records and make output easier for downstream loops.

- Semantic dedupe
- Similarity-based record merging
- Next-loop queue tables
- Record lifecycle states
- Human review state transitions

## v1.0.0 - Production Research Inbox

Primary goal: stable 24/7 research ingestion service.

- Long-running service mode
- Configurable schedules
- API for downstream loops
- Dashboard or review UI
- Observability logs
- Backup/export workflow
- Clear deployment docs
