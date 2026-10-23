"""Errores como application/problem+json (RFC 9457)."""

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.shared.domain.errors import ConflictError, DomainError, NotFoundError

logger = structlog.get_logger()

STATUS_BY_DOMAIN_ERROR: dict[type[DomainError], int] = {NotFoundError: 404, ConflictError: 409}


def problem(
    status: int, detail: str, headers: Mapping[str, str] | None = None, **extra: Any
) -> JSONResponse:
    body = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "request_id": structlog.contextvars.get_contextvars().get("request_id"),
        **extra,
    }
    return JSONResponse(
        jsonable_encoder(body), status, headers=headers, media_type="application/problem+json"
    )


async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
    status = next(
        (code for cls, code in STATUS_BY_DOMAIN_ERROR.items() if isinstance(exc, cls)), 422
    )
    return problem(status, str(exc))


async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return problem(422, "La solicitud tiene datos inválidos", errors=errors)


async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    return problem(exc.status_code, str(exc.detail), headers=exc.headers)


async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error")
    # Sin detalles internos en la respuesta: el request_id alcanza para buscar el log.
    return problem(500, "Error interno")


def register_problem_handlers(app: FastAPI) -> None:
    app.exception_handler(DomainError)(domain_error)
    app.exception_handler(RequestValidationError)(validation_error)
    app.exception_handler(HTTPException)(http_error)
    app.exception_handler(Exception)(unhandled_error)
