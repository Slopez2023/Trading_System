from __future__ import annotations

from research_loop.config import Settings


def test_settings_loads_openai_key_from_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=test-key",
                "RESEARCH_LOOP_EXTRACTOR=hybrid",
                "OPENAI_MODEL=gpt-test",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings.from_env(env_path=env_file)

    assert settings.openai_api_key == "test-key"
    assert settings.extractor_provider == "hybrid"
    assert settings.openai_model == "gpt-test"


def test_settings_defaults_to_cheap_openrouter_model(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=test-key",
                "OPENAI_BASE_URL=https://openrouter.ai/api/v1",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings.from_env(env_path=env_file)

    assert settings.openai_model == "qwen/qwen3-30b-a3b-instruct-2507"
    assert settings.max_output_tokens == 1200
