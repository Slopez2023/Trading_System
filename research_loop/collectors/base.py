from __future__ import annotations

from abc import ABC, abstractmethod

from research_loop.models import RawItem, Source


class CollectorError(RuntimeError):
    pass


class Collector(ABC):
    source_type: str

    @abstractmethod
    def collect(self, source: Source) -> list[RawItem]:
        raise NotImplementedError
