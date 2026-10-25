"""Configuración tipada, leída desde variables de entorno y `.env`."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, PostgresDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Solo para desarrollo: el validador de Settings lo rechaza en producción.
DEV_JWT_SECRET = "solo-para-desarrollo-no-usar-en-produccion"  # noqa: S105


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
    # HS256 pide al menos 32 bytes de clave (RFC 7518, sección 3.2).
    jwt_secret: SecretStr = Field(default=SecretStr(DEV_JWT_SECRET), min_length=32)
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    # Cotizaciones automáticas (PF-39): días hábiles cada 30 min en esas horas (sintaxis cron:
    # "10-17" es de 10:00 a 17:30); sábados y domingos, una vez a la hora diaria.
    dolarapi_url: str = "https://dolarapi.com/v1/dolares"
    fx_timezone: str = "America/Argentina/Buenos_Aires"
    fx_business_hours: str = "10-17"
    fx_daily_hour: int = 12

    @model_validator(mode="after")
    def _require_real_secret_in_production(self) -> Self:
        using_dev_secret = self.jwt_secret.get_secret_value() == DEV_JWT_SECRET
        if self.environment == "production" and using_dev_secret:
            raise ValueError("JWT_SECRET es obligatorio en producción")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
