from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExperimentSpec:
    source_record_id: str
    thesis: str
    experiment_type: str
    market: str
    asset: str = ""
    timeframes: list[str] = field(default_factory=list)
    data_needed: list[str] = field(default_factory=list)
    entry_rule: str = ""
    exit_rule: str = ""
    cost_model: list[str] = field(default_factory=list)
    success_metric: str = ""
    reject_if: str = ""
    status: str = "needs_data"
    scores: dict[str, int] = field(default_factory=dict)
    notes: str = ""

