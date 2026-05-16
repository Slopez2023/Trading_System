from __future__ import annotations

from research_loop.config import Settings
from research_loop.evaluation import run_extractor_eval


def test_local_extractor_eval_runs() -> None:
    score, lines = run_extractor_eval(Settings(extractor_provider="local"))

    assert 0 <= score <= 100
    assert any(line.startswith("score=") for line in lines)
