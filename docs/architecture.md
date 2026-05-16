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

The active v0.1.0 extractor is local and deterministic. It creates structured records from keywords, market hints, detected data requirements, risks, and source metadata.

The prompt files in `prompts/` define the planned LLM interface. A later version can add an LLM extractor behind the same pipeline without changing storage or collectors.

## Runtime Data

Runtime files are intentionally ignored:

- `data/*.sqlite3`
- `digests/*.md`
- `.env`

This keeps the GitHub repo clean while allowing local operation.
