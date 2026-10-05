"""Healthcheck de la API."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    # Un chequeo por dependencia externa; `database` se agrega en PF-19.
    checks: dict[str, Literal["ok", "error"]]


router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", checks={})
