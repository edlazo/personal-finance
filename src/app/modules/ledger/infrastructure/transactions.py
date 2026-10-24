"""Tabla y repositorio de movimientos."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.transaction import Transaction
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository


class TransactionModel(UserOwnedMixin, Base):
    __tablename__ = "transactions"
    # El listado (PF-34) filtra por usuario y ordena por fecha.
    __table_args__ = (Index("ix_transactions_user_id_date", "user_id", "date"),)

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id"), index=True)
    kind: Mapped[CategoryKind] = mapped_column(
        Enum(CategoryKind, name="transaction_kind", native_enum=False, length=10)
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    date: Mapped[date] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemyTransactionRepository(UserScopedRepository[TransactionModel]):
    model = TransactionModel

    async def add(self, transaction: Transaction) -> None:
        self.session.add(
            TransactionModel(
                id=transaction.id,
                user_id=transaction.user_id,
                account_id=transaction.account_id,
                category_id=transaction.category_id,
                kind=transaction.kind,
                amount=transaction.amount,
                date=transaction.date,
                description=transaction.description,
                created_at=transaction.created_at,
            )
        )
        await self.session.flush()
