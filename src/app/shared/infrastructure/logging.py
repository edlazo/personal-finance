"""Configuración de structlog: JSON fuera de local, consola legible en local."""

import structlog
from structlog.typing import Processor


def configure_logging(*, json_logs: bool) -> None:
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if json_logs:
        processors += [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(processors=processors)
