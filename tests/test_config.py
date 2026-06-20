"""Tests for env/.env configuration parsing."""

from __future__ import annotations

from euipo_tm_client.config import Settings, _load_dotenv


def test_load_dotenv_handles_quotes_comments_and_precedence(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        'EUIPO_API_KEY="abc123" # nomolith-dev\n'
        "EUIPO_API_SECRET = plainsecret # trailing note\n"
        '# a comment line\n'
        'EUIPO_ENVIRONMENT="sandbox"\n'
        "PRESET=fromfile\n"
    )

    for key in ("EUIPO_API_KEY", "EUIPO_API_SECRET", "EUIPO_ENVIRONMENT"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("PRESET", "fromenv")  # existing env vars must win

    _load_dotenv(env_file)

    settings = Settings.from_env(load_dotenv=False)
    assert settings.api_key == "abc123"  # quotes + inline comment stripped
    assert settings.api_secret == "plainsecret"  # unquoted inline comment stripped
    assert settings.environment == "sandbox"

    import os

    assert os.environ["PRESET"] == "fromenv"  # not overwritten by .env


def test_settings_urls_per_environment() -> None:
    sandbox = Settings(api_key="k", api_secret="s", environment="sandbox")
    production = Settings(api_key="k", api_secret="s", environment="production")
    assert sandbox.api_base_url == "https://api-sandbox.euipo.europa.eu/trademark-search"
    assert production.api_base_url == "https://api.euipo.europa.eu/trademark-search"
    assert "auth-sandbox" in sandbox.token_url
