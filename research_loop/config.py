from __future__ import annotations

from dataclasses import dataclass
import os
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
    extractor_provider: str = "local"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.2"
    openai_base_url: str = "https://api.openai.com/v1"

    @classmethod
    def from_env(
        cls,
        db_path: Path = DEFAULT_DB_PATH,
        digest_dir: Path = DEFAULT_DIGEST_DIR,
        extractor_provider: str | None = None,
        openai_model: str | None = None,
    ) -> "Settings":
        return cls(
            db_path=db_path,
            digest_dir=digest_dir,
            request_timeout_seconds=int(os.getenv("RESEARCH_LOOP_TIMEOUT_SECONDS", "20")),
            user_agent=os.getenv("RESEARCH_LOOP_USER_AGENT", "TradingResearchLoop/0.1.0"),
            extractor_provider=extractor_provider or os.getenv("RESEARCH_LOOP_EXTRACTOR", "local"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=openai_model or os.getenv("OPENAI_MODEL", "gpt-5.2"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
