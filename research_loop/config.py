from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "research_loop.sqlite3"
DEFAULT_DIGEST_DIR = ROOT / "digests"


@dataclass(frozen=True)
class Settings:
    db_path: Path = DEFAULT_DB_PATH
    digest_dir: Path = DEFAULT_DIGEST_DIR
    request_timeout_seconds: int = 20
    user_agent: str = "TradingResearchLoop/0.1.0"
