"""Casos de uso: editar y borrar movimientos (una transferencia, por sus dos patas)."""

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.ledger.application.create_transaction import TransactionsUnitOfWork
from app.modules.ledger.domain.account import AccountArchivedError
from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.transaction import (
    InvalidTransactionError,
    Transaction,
    check_movement,
)


async def _editable_legs(uow: TransactionsUnitOfWork, transaction_id: UUID) -> list[Transaction]:
    """El movimiento, o las dos patas si es una transferencia; nunca de una cuenta archivada."""
    transaction = await uow.transactions.get_transaction(transaction_id)
    if transaction.trade_id is not None:
        raise InvalidTransactionError(
            "Los movimientos de una operación de inversión no se editan ni se borran"
        )
    legs = [transaction]
    if transaction.transfer_group_id is not None:
        legs = await uow.transactions.transfer_legs(transaction.transfer_group_id)
    for leg in legs:
        if (await uow.accounts.get_account(leg.account_id)).archived_at is not None:
            raise AccountArchivedError
    return legs


@dataclass(frozen=True)
class UpdateTransaction:
    uow: TransactionsUnitOfWork

    async def __call__(
        self,
        transaction_id: UUID,
        *,
        account_id: UUID | None = None,
        kind: CategoryKind | None = None,
        category_id: UUID | None = None,
        amount: Decimal | None = None,
        on: date | None = None,
        description: str | None = None,
    ) -> Transaction:
        """Lo que queda en None no cambia; una descripción vacía la borra."""
        async with self.uow:
            legs = await _editable_legs(self.uow, transaction_id)
            moves = (account_id, kind, category_id) != (None, None, None)
            if legs[0].transfer_group_id is not None and moves:
                raise InvalidTransactionError(
                    "En una transferencia solo se editan el monto, la fecha y la descripción"
                )
            # Compra o venta de dólares: cada pata tiene su monto y solo cambia la editada.
            accounts = [await self.uow.accounts.get_account(leg.account_id) for leg in legs]
            own_amounts = len({account.currency for account in accounts}) > 1

            def new_amount(leg: Transaction) -> Decimal:
                if amount is None or (own_amounts and leg.id != transaction_id):
                    return leg.amount
                return amount

            # replace() vuelve a validar el monto y limpia la descripción.
            edited = [
                replace(
                    leg,
                    account_id=account_id or leg.account_id,
                    kind=kind or leg.kind,
                    category_id=category_id or leg.category_id,
                    amount=new_amount(leg),
                    date=on or leg.date,
                    description=leg.description if description is None else description,
                )
                for leg in legs
            ]
            movement = edited[0]
            # Si cambian cuenta, tipo o categoría no es transferencia: hay una sola pata.
            if moves and movement.category_id is not None:
                account = await self.uow.accounts.get_account(movement.account_id)
                category = await self.uow.categories.get_category(movement.category_id)
                check_movement(movement.kind, account, category)
            for leg in edited:
                await self.uow.transactions.save(leg)
            await self.uow.commit()
        return next(leg for leg in edited if leg.id == transaction_id)


@dataclass(frozen=True)
class DeleteTransaction:
    uow: TransactionsUnitOfWork

    async def __call__(self, transaction_id: UUID) -> None:
        async with self.uow:
            for leg in await _editable_legs(self.uow, transaction_id):
                await self.uow.transactions.delete(leg.id)
            await self.uow.commit()
