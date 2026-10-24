"""Dobles en memoria para los casos de uso de cuentas."""

from types import TracebackType
from typing import Self
from uuid import UUID

from app.modules.ledger.domain.account import Account, same_name
from app.shared.domain.errors import NotFoundError


class InMemoryAccounts:
    def __init__(self) -> None:
        self.items: dict[UUID, Account] = {}

    async def name_taken(self, name: str, *, excluding: UUID | None = None) -> bool:
        return any(
            same_name(a.name) == same_name(name) and a.archived_at is None and a.id != excluding
            for a in self.items.values()
        )

    async def add(self, account: Account) -> None:
        self.items[account.id] = account

    async def get_account(self, account_id: UUID) -> Account:
        if account_id not in self.items:
            raise NotFoundError("El recurso no existe")
        return self.items[account_id]

    async def list_accounts(self, *, include_archived: bool) -> list[Account]:
        return [a for a in self.items.values() if include_archived or a.archived_at is None]

    async def save(self, account: Account) -> None:
        self.items[account.id] = account


class FakeAccountsUnitOfWork:
    def __init__(self) -> None:
        self.accounts = InMemoryAccounts()
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass
