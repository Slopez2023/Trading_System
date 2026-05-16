from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Source:
    source_id: str
    source_type: str
    name: str
    url: str
    markets: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    status: str = "active"
    check_frequency_minutes: int = 60
    quality_score: float = 0.5
    noise_score: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RawItem:
    source_id: str
    source_type: str
    url: str
    title: str
    text: str
    author: str = ""
    published_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchRecord:
    record_type: str
    title: str
    summary: str
    details: str = ""
    markets: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    timeframes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    required_data: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)
    status: str = "captured"
    next_loop_targets: list[str] = field(default_factory=list)
    evidence_summary: str = ""
    evidence_relationship: str = "source_observation"
