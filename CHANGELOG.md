# Changelog

## 0.1.0 - 2026-05-16

- Added SQLite-backed source registry, raw item storage, research records, evidence links, and source performance tables.
- Added Reddit JSON and RSS collectors.
- Added deterministic local research extractor and scorer.
- Added CLI commands for initialization, source seeding, collection, extraction, digests, stats, manual raw item input, and continuous looping.
- Added prompt templates for future LLM-backed classification, extraction, and scoring.
- Added unit tests for extraction and repository behavior.

## Unreleased

- Added OpenAI extraction provider using structured JSON output.
- Added `local`, `openai`, and `hybrid` extractor modes.
- Added environment-based OpenAI configuration.
- Added local `.env` loading for OpenAI configuration.
- Documented OpenRouter/OpenAI-compatible provider configuration.
- Added OpenRouter chat-completions support and set DeepSeek V4 Flash as the low-cost default model.
- Fixed local strategy/risk classification so strategy ideas with risk terms stay strategy ideas.
- Trimmed roadmap/checklist scope to v0.3.0.
- Added source scheduling, source error tracking, raw item processing claim states, source/raw CLI commands, and smoke-test command.
- Added extractor quality evaluation command with curated benchmark cases.
- Improved local risk-warning classification based on extractor evaluation results.
- Added terminal monitor command for live CLI observability.
- Added `OPENROUTER_API_KEY` support for OpenRouter-only setup.
