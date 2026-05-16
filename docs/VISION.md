# Vision

Build a 24/7 research ingestion system that continuously discovers, stores, and organizes trading research inputs for downstream loops.

The loop should behave like a source-backed research memory:

```text
I found this.
I saved the original evidence.
I extracted what it might mean.
I linked it to sources.
I routed it to the next loop.
```

## Goal

Create a clean, reliable research inbox that captures:

- Strategy ideas
- Market observations
- Risk warnings
- Data needs
- Research questions
- Source candidates
- Event catalysts
- Market themes
- Contradictions

The system should be broad enough to catch weak signals early, but structured enough that other loops can consume the output without guessing.

## Non-Goals

This loop should not:

- Place trades
- Build bots
- Claim an idea is profitable
- Skip source storage
- Treat AI output as truth
- Mix raw collection with downstream execution

## Operating Principles

- Save raw evidence before analysis.
- Link every research record back to sources.
- Keep collectors, extractors, scorers, and routers separate.
- Prefer structured records over loose notes.
- Make every idea auditable.
- Let source quality improve over time.
- Keep the first versions boring and inspectable.

## Long-Term Direction

The mature version should include:

- LLM-backed extraction and scoring
- Semantic deduplication
- Source quality tracking
- More source adapters
- API access for downstream loops
- Dashboard review workflow
- Scheduled 24/7 deployment
- Human approval paths for source changes
