# Architecture

The repo is organized as a loop-based system. The current production code is the research loop; later loops should be added beside it and consume its outputs through a stable contract.

```text
loops/
  research_loop/
  next_loop/
  another_loop/

research_loop/          current Python package and CLI
```

The research loop is intentionally split into small stages:

```text
Source Registry
  -> Collectors
  -> Raw Items
  -> Extractor
  -> Research Records
  -> Evidence Links
  -> Digest / Downstream Loops
```

## Multi-Loop Direction

Each loop should have a clear job, storage boundary, and output contract.

```text
Research Loop
  -> captures source-backed ideas
  -> outputs research_records + evidence_links

Future Validation Loop
  -> reads research records
  -> decides what needs data or backtesting

Future Backtest Loop
  -> reads validated strategy ideas
  -> produces test results

Future Bot/Execution Loop
  -> only consumes approved, risk-checked outputs
```

The research loop should not know how later loops trade. Later loops should not mutate raw research evidence.

## Storage

SQLite is the v0.3.0 storage backend.

Main tables:

- `sources`: saved places to collect from.
- `raw_items`: original evidence exactly as collected.
- `research_records`: clean strategy ideas, observations, warnings, questions, and data needs.
- `evidence_links`: links between clean records and raw evidence.
- `source_performance`: counters for later source quality scoring.

## Collectors

Collectors only fetch and normalize raw source items. They do not create strategy ideas.

Included collectors:

- RSS / Atom feeds
- Reddit JSON feeds

## Extraction

The default extractor is local and deterministic. It creates structured records from keywords, market hints, detected data requirements, risks, and source metadata.

The AI extractor can be enabled with `RESEARCH_LOOP_EXTRACTOR=openai` or `RESEARCH_LOOP_EXTRACTOR=hybrid`. The setting name is `openai` because the code uses an OpenAI-compatible HTTP shape, but the recommended provider for this repo is OpenRouter. Hybrid mode tries AI first and falls back to the local extractor if the API key or API call fails.

The extractor uses OpenRouter chat completions when `OPENAI_BASE_URL=https://openrouter.ai/api/v1`. It uses OpenAI Responses API only when pointed at the OpenAI base URL. The prompt files in `prompts/` document the extraction intent and can be refined as the AI path improves.

Auth uses `OPENROUTER_API_KEY` from the shell environment or local `.env`. `OPENAI_API_KEY` is also supported for compatibility, but Codex login/session files are not read by this project.

OpenRouter and other OpenAI-compatible providers can be used by setting `OPENAI_BASE_URL` and `OPENAI_MODEL`.

The recommended low-cost OpenRouter model for this project is `deepseek/deepseek-v4-flash`. OpenRouter also lists `deepseek/deepseek-v4-flash:free`, but the paid low-cost endpoint is the safer default for reliability.

## Downstream Boundary

Downstream loops should consume:

- `research_records` for the structured idea.
- `evidence_links` for source support.
- `raw_items` only when they need to inspect original evidence.

They should avoid depending on extractor internals, prompt wording, or CLI display formatting.

## Runtime Data

Runtime files are intentionally ignored:

- `data/*.sqlite3`
- `digests/*.md`
- `.env`

This keeps the GitHub repo clean while allowing local operation.
