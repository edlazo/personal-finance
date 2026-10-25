"""Implementación de `CashMovements` (app.shared) para los otros módulos."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.transaction import Transaction
from app.modules.ledger.infrastructure.accounts import SqlAlchemyAccountRepository
from app.modules.ledger.infrastructure.transactions import SqlAlchemyTransactionRepository
from app.shared.domain.cash import CashAccount


class LedgerCashMovements:
    """Usa la sesión de quien lo pide: el movimiento se guarda en su misma transacción."""

    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.user_id = user_id
        self.accounts = SqlAlchemyAccountRepository(session, user_id)
        self.transactions = SqlAlchemyTransactionRepository(session, user_id)

    async def account(self, account_id: UUID) -> CashAccount:
        account = await self.accounts.get_account(account_id)
        return CashAccount(
            account.id, account.currency, account.holds_investments, account.archived_at is not None
        )

    async def record_trade(
        self,
        account_id: UUID,
        amount: Decimal,
        *,
        incoming: bool,
        on: date,
        trade_id: UUID,
        description: str,
    ) -> None:
        kind = CategoryKind.INCOME if incoming else CategoryKind.EXPENSE
        movement = Transaction(
            self.user_id, account_id, kind, amount, on, None, description, trade_id=trade_id
        )
        await self.transactions.add(movement)
