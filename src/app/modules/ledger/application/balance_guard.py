"""Control común: ningún cambio deja una cuenta en negativo (salvo las comitentes)."""

from datetime import date
from typing import Protocol
from uuid import UUID

from app.modules.ledger.domain.account import AccountRepository, check_non_negative
from app.modules.ledger.domain.transaction import TransactionRepository


class BalanceReader(Protocol):
    @property
    def accounts(self) -> AccountRepository: ...

    @property
    def transactions(self) -> TransactionRepository: ...


async def ensure_non_negative(uow: BalanceReader, touched: dict[UUID, date]) -> None:
    """Se llama después de guardar el cambio y antes del commit, con la fecha más vieja tocada
    de cada cuenta: un movimiento con fecha pasada tampoco puede dejar negativo un saldo
    posterior."""
    for account_id, since in touched.items():
        account = await uow.accounts.get_account(account_id)
        check_non_negative(account, await uow.transactions.daily_totals(account_id), since)
