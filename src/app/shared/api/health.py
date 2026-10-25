"""Healthcheck de la API."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncEngine

from app.shared.api.dependencies import get_engine
from app.shared.infrastructure.database import ping

CheckStatus = Literal["ok", "error"]


class HealthResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "ok", "checks": {"database": "ok"}}]}
    )

    status: CheckStatus
    checks: dict[str, CheckStatus]


async def database_check(engine: Annotated[AsyncEngine, Depends(get_engine)]) -> bool:
    return await ping(engine)


router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Estado de la API y sus dependencias",
    description="Responde 200 si todas las dependencias están disponibles y 503 si alguna falla.",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": HealthResponse,
            "description": "Alguna dependencia no responde",
            "content": {
                "application/json": {
                    "example": {"status": "error", "checks": {"database": "error"}}
                }
            },
        }
    },
)
async def health(
    response: Response, database_ok: Annotated[bool, Depends(database_check)]
) -> HealthResponse:
    if database_ok:
        return HealthResponse(status="ok", checks={"database": "ok"})
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="error", checks={"database": "error"})
