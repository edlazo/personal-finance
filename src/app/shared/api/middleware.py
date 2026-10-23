"""Middleware HTTP: request_id y log de cada request."""

import re
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

import structlog
from fastapi import Request, Response

logger = structlog.get_logger()

# El header viene del cliente: solo se reutiliza si no puede ensuciar los logs.
SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")


async def request_logging(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    incoming = request.headers.get("x-request-id", "")
    request_id = incoming if SAFE_REQUEST_ID.fullmatch(incoming) else uuid4().hex
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start = perf_counter()
    status = 500  # si la vista lanza una excepción no manejada
    try:
        response = await call_next(request)
        status = response.status_code
    finally:
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=status,
            duration_ms=round((perf_counter() - start) * 1000, 1),
        )
    response.headers["X-Request-ID"] = request_id
    return response
