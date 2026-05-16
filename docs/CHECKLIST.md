# Project Checklist

This is the high-level checklist. The detailed version-by-version plan lives in [ROADMAP.md](ROADMAP.md).

## Repo Health

- [x] Git repo initialized
- [x] README added
- [x] Changelog added
- [x] Vision doc added
- [x] Roadmap added
- [x] Architecture doc added
- [x] GitHub Actions test workflow added
- [x] Runtime database files ignored
- [x] Runtime digest files ignored
- [x] Environment example added
- [x] Contributing guide added
- [x] Issue templates added
- [x] Pull request template added
- [ ] License confirmed
- [ ] Remote GitHub repository connected
- [ ] Branch protection enabled on GitHub

## Current Product Boundary

- [x] Research ingestion only
- [x] No trading execution
- [x] Raw evidence saved before analysis
- [x] Research records linked to evidence
- [ ] Stable downstream output schema documented
- [ ] API/export contract documented

## v0.1.x Foundation and Hardening

- [x] SQLite schema
- [x] Source registry
- [x] Raw item storage
- [x] Research record storage
- [x] Evidence links
- [x] RSS collector
- [x] Reddit collector
- [x] Local extractor
- [x] CLI commands
- [x] Digest generation
- [x] Unit tests
- [ ] Fix strategy/risk classification issue
- [ ] Respect source schedules
- [ ] Add processing claim states
- [ ] Store collector failures
- [ ] Add structured logging
- [ ] Add source CLI management
- [ ] Add collector fixture tests

## v0.2.x AI Extraction

- [ ] Extractor interface
- [ ] OpenAI extractor
- [ ] Local fallback
- [ ] Strict JSON schema
- [ ] Prompt versioning
- [ ] Model output validation
- [ ] Cost/token tracking
- [ ] AI fixture tests
- [ ] Extractor evaluation set

## v0.3.x Source Management

- [ ] `sources.yaml`
- [ ] Source import/export
- [ ] Source add/update/list/disable commands
- [ ] Source health checks
- [ ] Source performance scoring
- [ ] Source candidate workflow
- [ ] Source approval/rejection flow

## v0.4.x Source Expansion

- [ ] Exchange announcements
- [ ] SEC filings
- [ ] Economic calendar
- [ ] News RSS bundle
- [ ] Funding rates
- [ ] Open interest
- [ ] Liquidation data decision
- [ ] X/social integration decision
- [ ] Collector rate-limit handling

## v0.5.x Dedupe and Routing

- [ ] Exact record dedupe
- [ ] Semantic dedupe
- [ ] Merge evidence
- [ ] Canonical records
- [ ] Record lifecycle statuses
- [ ] Routing queues
- [ ] Downstream loop handoff schemas
- [ ] Route history

## v0.6.x Service Readiness

- [ ] Service mode
- [ ] Graceful shutdown
- [ ] Process guard
- [ ] Retry/backoff
- [ ] Dead-letter handling
- [ ] Health command
- [ ] Backup command
- [ ] Maintenance command
- [ ] Local Mac deployment docs
- [ ] Docker deployment docs

## v0.7.x API and Exports

- [ ] JSON export
- [ ] CSV export
- [ ] Stable schema versioning
- [ ] HTTP API
- [ ] Read-only API mode
- [ ] API tests

## v0.8.x Review Workflow

- [ ] Review commands
- [ ] Record notes
- [ ] Promote/reject commands
- [ ] Evidence display
- [ ] Review digest
- [ ] Dashboard decision

## v0.9.x Production Polish

- [ ] Documentation pass
- [ ] Security pass
- [ ] Performance pass
- [ ] Migration pass
- [ ] Load test
- [ ] Backup/restore test
- [ ] Upgrade test

## v1.0.0 Stable Research Inbox

- [ ] 24/7 operation
- [ ] Reliable source scheduling
- [ ] AI extraction with fallback
- [ ] Evidence-linked records
- [ ] Dedupe and merge
- [ ] Downstream queue/API/export
- [ ] Review workflow
- [ ] Observability
- [ ] Backup/restore
- [ ] Full test suite
