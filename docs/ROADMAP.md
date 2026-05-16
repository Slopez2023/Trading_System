# Roadmap

This project is a research ingestion loop, not a trading bot. It collects source evidence, extracts structured research records, and prepares those records for later loops.

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

## v0.1.1 - Working AI Version

Purpose: make the loop useful now by adding AI extraction while keeping local fallback.

- [x] Add extractor provider setting: `local`, `openai`, `hybrid`
- [x] Add OpenAI extractor
- [x] Use structured JSON output
- [x] Validate model output before saving records
- [x] Keep local extractor as fallback
- [x] Fix strategy/risk classification issue in local extractor
- [x] Add tests for OpenAI response parsing
- [x] Add real `.env` loading or document shell exports clearly
- [x] Add one command that runs a full smoke test
- [x] Add source scheduling so sources are only checked when due
- [x] Store collector errors instead of only printing them
- [ ] Add structured logging

Acceptance:

- [x] Local extraction works without API keys
- [x] OpenAI extraction can be tested without live API calls
- [x] Hybrid mode falls back to local extraction
- [ ] User can run one documented AI smoke test with `OPENAI_API_KEY`

## v0.2.0 - Source and Loop Hardening

Purpose: make the system safe for long-running use.

- [x] Respect `check_frequency_minutes`
- [x] Add source due/not-due logic
- [x] Add raw item states: `pending`, `processing`, `extracted`, `ignored`, `failed`
- [x] Add processing claim step to avoid duplicate processing
- [x] Store source failures in database
- [x] Add commands: `sources list`, `sources enable`, `sources disable`
- [x] Add command: `raw list --status pending`
- [ ] Add collector fixture tests
- [x] Add integration test: `init-db -> add-raw -> extract -> digest`

Acceptance:

- [x] Running the loop repeatedly does not over-fetch sources
- [x] Collection failures are inspectable
- [x] Two workers cannot process the same raw item

## v0.3.0 - Clean Source Management

Purpose: make source management editable without changing code.

- [ ] Add `sources.yaml`
- [ ] Add source import/export commands
- [ ] Add source validation
- [ ] Add source categories: social, news, exchange, research, market_data, filing
- [ ] Add source candidate workflow
- [ ] Add source performance scoring
- [ ] Add source health command
- [ ] Add first exchange/news source pack

Acceptance:

- [ ] Sources can be added/edited outside Python code
- [ ] Source quality is visible
- [ ] Candidate sources require approval before activation

## Later

- Record dedupe and merge
- Downstream routing queues
- API/export layer
- Review dashboard
- 24/7 service deployment
