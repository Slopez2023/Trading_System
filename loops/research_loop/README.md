# Research Loop

Status: working, being hardened for `v0.3.0`.

The research loop is the first loop in the system.

```text
Sources -> Raw Items -> AI/Local Extraction -> Research Records -> Evidence Links -> Downstream Loops
```

## Implementation

The Python package currently lives at:

```text
research_loop/
```

The CLI is:

```bash
python3 -m research_loop
```

This folder owns the loop-level docs and contract. The code package stays at the repo root for now to keep imports, packaging, and tests simple.

## Inputs

- RSS sources
- Reddit JSON sources
- Manual raw items
- Future exchange/news/source packs

## Outputs

- SQLite research records
- SQLite evidence links
- SQLite raw evidence
- Markdown digests

## Main Commands

```bash
python3 -m research_loop init-db
python3 -m research_loop sources import --file loops/research_loop/sources.json
python3 -m research_loop run-once
python3 -m research_loop loop --sleep-seconds 900
python3 -m research_loop monitor
python3 -m research_loop smoke-test
python3 -m research_loop records export --file /tmp/research_records.json
```

## v0.3.0 Goal

Make this loop deployable and dependable enough that the next loops can build against it.

Done:

- AI extraction through OpenRouter-compatible API
- Local fallback extraction
- Monitor CLI
- Normalization
- Conservative duplicate merging
- Evidence preservation
- JSON source config import/export
- Downstream record export
- Structured JSONL runtime logs

Still needed:

- More source packs
- Deployment runbook completion
