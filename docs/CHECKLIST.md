# Project Checklist

Use this as the working checklist for moving the project from v0.1.0 to a real research engine.

## Repo Health

- [x] Git repo initialized
- [x] README added
- [x] Changelog added
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

## v0.1.0 Core

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

## Near-Term Engineering

- [ ] Add real extractor interface
- [ ] Add OpenAI extractor
- [ ] Validate LLM JSON output
- [ ] Add source import/export
- [ ] Add record dedupe
- [ ] Add source performance scoring
- [ ] Add logging
- [ ] Add config file support
- [ ] Add scheduled service instructions

## Source Expansion

- [ ] Exchange announcements
- [ ] Funding rates
- [ ] Open interest
- [ ] SEC filings
- [ ] Economic calendar
- [ ] News RSS bundle
- [ ] Quant research feeds
- [ ] X integration decision

## Downstream Readiness

- [ ] Stable output schema documented
- [ ] Queue format for downstream loops
- [ ] API or export command
- [ ] Record status transitions
- [ ] Human review workflow
- [ ] Backtest-loop handoff contract
