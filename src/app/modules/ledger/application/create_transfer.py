"""Caso de uso: transferir entre dos cuentas propias, en la misma moneda o comprando dólares."""

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.ledger.application.create_transaction import TransactionsUnitOfWork
from app.modules.ledger.application.list_categories import ensure_default_categories
from app.modules.ledger.domain.account import Account
from app.modules.ledger.domain.category import Category, CategoryKind
from app.modules.ledger.domain.transaction import Transaction, Transfer, transfer

FEES = "Comisiones"


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
        received: Decimal | None = None,
        fee: Decimal | None = None,
    ) -> Transfer:
        async with self.uow:
            # get_account da 404 si la cuenta es de otro usuario.
            source = await self.uow.accounts.get_account(source_id)
            target = await self.uow.accounts.get_account(target_id)
            result = transfer(user_id, source, target, amount, on, description, received)
            await self.uow.transactions.add(result.outgoing)
            await self.uow.transactions.add(result.incoming)
            if fee is not None:
                result = replace(result, fee=await self._charge_fee(user_id, source, fee, on))
            await self.uow.commit()
        return result

    async def _charge_fee(
        self, user_id: UUID, source: Account, fee: Decimal, on: date
    ) -> Transaction:
        """Decisión del PO: la comisión es un gasto aparte en el origen, en "Comisiones"."""
        await ensure_default_categories(self.uow, user_id)
        categories = await self.uow.categories.list_categories()
        fees = next(
            (
                c
                for c in categories
                if c.kind is CategoryKind.EXPENSE
                and c.parent_id is None
                and c.name.lower() == FEES.lower()
            ),
            None,
        )
        if fees is None:
            # Los usuarios anteriores a esta versión no la tienen entre las por defecto.
            fees = Category(user_id, FEES, CategoryKind.EXPENSE)
            await self.uow.categories.add(fees)
        charged = Transaction(
            user_id, source.id, CategoryKind.EXPENSE, fee, on, fees.id, "Comisión"
        )
        await self.uow.transactions.add(charged)
        return charged
