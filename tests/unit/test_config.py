from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings

ENV_EXAMPLE = Path(__file__).parents[2] / ".env.example"


def test_defaults_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    settings = Settings(_env_file=None)

    assert settings.environment == "local"
    assert settings.debug is False


def test_reads_dotenv_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ENVIRONMENT=production\nDEBUG=true\n", encoding="utf-8")

    settings = Settings(_env_file=env_file)

    assert settings.environment == "production"
    assert settings.debug is True


def test_env_var_overrides_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ENVIRONMENT=production\n", encoding="utf-8")
    monkeypatch.setenv("ENVIRONMENT", "test")

    assert Settings(_env_file=env_file).environment == "test"


def test_rejects_unknown_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_env_example_is_valid() -> None:
    assert Settings(_env_file=ENV_EXAMPLE).environment == "local"


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
