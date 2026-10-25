"""Caso de uso: transferir entre dos cuentas propias de la misma moneda."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.ledger.application.create_transaction import TransactionsUnitOfWork
from app.modules.ledger.domain.transaction import Transfer, transfer


@dataclass(frozen=True)
class CreateTransfer:
    uow: TransactionsUnitOfWork

    async def __call__(
        self,
        user_id: UUID,
        *,
        source_id: UUID,
        target_id: UUID,
        amount: Decimal,
        on: date,
        description: str | None = None,
    ) -> Transfer:
        async with self.uow:
            # get_account da 404 si la cuenta es de otro usuario.
            source = await self.uow.accounts.get_account(source_id)
            target = await self.uow.accounts.get_account(target_id)
            result = transfer(user_id, source, target, amount, on, description)
            await self.uow.transactions.add(result.outgoing)
            await self.uow.transactions.add(result.incoming)
            await self.uow.commit()
        return result
