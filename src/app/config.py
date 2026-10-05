"""Configuración tipada, leída desde variables de entorno y `.env`."""

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Las variables de entorno tienen prioridad sobre `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Personal Finance API"
    environment: Literal["local", "test", "production"] = "local"
    debug: bool = False
    # Default: Postgres local de desarrollo (docker compose, PF-18).
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/personal_finance"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
