# Contributing

This project should stay modular and auditable.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

## Design Rules

- Collectors fetch raw items only.
- Extractors create structured research records only.
- Storage code owns database reads and writes.
- Every research record should link back to raw evidence.
- Do not add trading execution logic to this repo.
- Do not commit `.env`, SQLite databases, generated digests, or caches.

## Testing

Run before committing:

```bash
python3 -m pytest
python3 -m compileall research_loop tests
```

## Pull Requests

Good PRs should include:

- Clear purpose
- Small scope
- Tests for changed behavior
- Notes on source/API changes
- Notes on schema changes, if any

## Schema Changes

If changing database tables:

- Update `research_loop/db.py`
- Update `docs/architecture.md`
- Add or update tests
- Mention migration impact in the PR
