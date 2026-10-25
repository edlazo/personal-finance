"""Puerto de Unit of Work: delimita una transacción de negocio."""

from types import TracebackType
from typing import Protocol, Self


class UnitOfWork(Protocol):
    """Lo que no se confirma con `commit()` se descarta al salir del bloque `async with`."""

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
