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
        model = openai_model or value("OPENAI_MODEL", _default_model_for_base_url(base_url))
        return cls(
            db_path=db_path,
            digest_dir=digest_dir,
            request_timeout_seconds=int(value("RESEARCH_LOOP_TIMEOUT_SECONDS", "20")),
            user_agent=value("RESEARCH_LOOP_USER_AGENT", "TradingResearchLoop/0.1.0"),
            extractor_provider=extractor_provider or value("RESEARCH_LOOP_EXTRACTOR", "local"),
            openai_api_key=value("OPENAI_API_KEY"),
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
        return "qwen/qwen3-30b-a3b-instruct-2507"
    return "gpt-5.2"
