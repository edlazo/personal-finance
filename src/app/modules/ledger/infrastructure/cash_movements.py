"""Implementación de `CashMovements` (app.shared) para los otros módulos."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ledger.domain.account import check_non_negative
from app.modules.ledger.domain.category import Category, CategoryKind, default_categories
from app.modules.ledger.domain.transaction import Transaction
from app.modules.ledger.infrastructure.accounts import SqlAlchemyAccountRepository
from app.modules.ledger.infrastructure.persistence import SqlAlchemyCategoryRepository
from app.modules.ledger.infrastructure.transactions import SqlAlchemyTransactionRepository
from app.shared.domain.cash import CashAccount

INCOME_CATEGORY = "Rentas"


class LedgerCashMovements:
    """Usa la sesión de quien lo pide: el movimiento se guarda en su misma transacción."""

    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.user_id = user_id
        self.accounts = SqlAlchemyAccountRepository(session, user_id)
        self.transactions = SqlAlchemyTransactionRepository(session, user_id)
        self.categories = SqlAlchemyCategoryRepository(session, user_id)

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
        if not incoming:
            # Una compra tampoco puede dejar en negativo una wallet (decisión del PO, US-062).
            account = await self.accounts.get_account(account_id)
            check_non_negative(account, await self.transactions.daily_totals(account_id), on)

    async def record_income(
        self, account_id: UUID, amount: Decimal, *, on: date, trade_id: UUID, description: str
    ) -> None:
        category = await self._income_category()
        movement = Transaction(
            self.user_id,
            account_id,
            CategoryKind.INCOME,
            amount,
            on,
            category.id,
            description,
            trade_id=trade_id,
        )
        await self.transactions.add(movement)

    async def _income_category(self) -> Category:
        """La de "Rentas"; sin commit propio, para no partir la transacción de quien llama."""
        if not await self.categories.has_any():
            # Primer uso: las por defecto (decisión del PO del Sprint 4) ya traen "Rentas".
            await self.categories.add_defaults(default_categories(self.user_id))
        for category in await self.categories.list_categories():
            top_income = category.kind is CategoryKind.INCOME and category.parent_id is None
            if top_income and category.name.lower() == INCOME_CATEGORY.lower():
                return category
        # El usuario la archivó: se crea una nueva.
        category = Category(self.user_id, INCOME_CATEGORY, CategoryKind.INCOME)
        await self.categories.add(category)
        return category
