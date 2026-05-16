# Architecture

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

## Storage

SQLite is the v0.1.0 storage backend.

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

The OpenAI extractor can be enabled with `RESEARCH_LOOP_EXTRACTOR=openai` or `RESEARCH_LOOP_EXTRACTOR=hybrid`. Hybrid mode tries OpenAI first and falls back to the local extractor if the API key or API call fails.

The OpenAI extractor uses the Responses API with structured JSON output. The prompt files in `prompts/` document the extraction intent and can be refined as the AI path improves.

Auth uses `OPENAI_API_KEY` from the shell environment or local `.env`. Codex login/session files are not read by this project.

## Runtime Data

Runtime files are intentionally ignored:

- `data/*.sqlite3`
- `digests/*.md`
- `.env`

This keeps the GitHub repo clean while allowing local operation.
