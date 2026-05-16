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
