from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "research_loop.sqlite3"
DEFAULT_DIGEST_DIR = ROOT / "digests"
DEFAULT_LOG_PATH = ROOT / "logs" / "research_loop.jsonl"


@dataclass(frozen=True)
class Settings:
    db_path: Path = DEFAULT_DB_PATH
    digest_dir: Path = DEFAULT_DIGEST_DIR
    log_path: Path = DEFAULT_LOG_PATH
    request_timeout_seconds: int = 20
    user_agent: str = "TradingResearchLoop/0.3.1"
    extractor_provider: str = "local"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.2"
    openai_base_url: str = "https://api.openai.com/v1"
    max_output_tokens: int = 1200

    @classmethod
    def from_env(
        cls,
        db_path: Path = DEFAULT_DB_PATH,
        digest_dir: Path = DEFAULT_DIGEST_DIR,
        extractor_provider: str | None = None,
        openai_model: str | None = None,
        env_path: Path | None = None,
    ) -> "Settings":
        file_env = _load_env_file(env_path or Path.cwd() / ".env")

        def value(name: str, default: str = "") -> str:
            return os.getenv(name) or file_env.get(name) or default

        base_url = value("OPENAI_BASE_URL", "https://api.openai.com/v1")
        provider_key = value("OPENROUTER_API_KEY") or value("OPENAI_API_KEY")
        model = openai_model or value("OPENAI_MODEL", _default_model_for_base_url(base_url))
        resolved_db_path = Path(value("RESEARCH_LOOP_DB_PATH", str(db_path))) if db_path == DEFAULT_DB_PATH else db_path
        resolved_digest_dir = (
            Path(value("RESEARCH_LOOP_DIGEST_DIR", str(digest_dir))) if digest_dir == DEFAULT_DIGEST_DIR else digest_dir
        )
        return cls(
            db_path=resolved_db_path,
            digest_dir=resolved_digest_dir,
            log_path=Path(value("RESEARCH_LOOP_LOG_PATH", str(DEFAULT_LOG_PATH))),
            request_timeout_seconds=int(value("RESEARCH_LOOP_TIMEOUT_SECONDS", "20")),
            user_agent=value("RESEARCH_LOOP_USER_AGENT", "TradingResearchLoop/0.3.1"),
            extractor_provider=extractor_provider or value("RESEARCH_LOOP_EXTRACTOR", "local"),
            openai_api_key=provider_key,
            openai_model=model,
            openai_base_url=base_url,
            max_output_tokens=int(value("RESEARCH_LOOP_MAX_OUTPUT_TOKENS", "1200")),
        )


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = raw_value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _default_model_for_base_url(base_url: str) -> str:
    if "openrouter.ai" in base_url:
        return "deepseek/deepseek-v4-flash"
    return "gpt-5.2"
