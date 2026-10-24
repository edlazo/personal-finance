"""Tabla y repositorio de movimientos."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, func, select
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.transaction import Transaction, TransactionFilter
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

    async def search(
        self, filters: TransactionFilter, *, limit: int, offset: int
    ) -> tuple[list[Transaction], int]:
        query = self.scoped()
        m = TransactionModel
        if filters.date_from is not None:
            query = query.where(m.date >= filters.date_from)
        if filters.date_to is not None:
            query = query.where(m.date <= filters.date_to)
        if filters.account_id is not None:
            query = query.where(m.account_id == filters.account_id)
        if filters.category_ids is not None:
            query = query.where(m.category_id.in_(filters.category_ids))
        if filters.kind is not None:
            query = query.where(m.kind == filters.kind)
        if filters.text:
            escaped = filters.text.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
            query = query.where(m.description.ilike(f"%{escaped}%", escape="\\"))
        if filters.amount_min is not None:
            query = query.where(m.amount >= filters.amount_min)
        if filters.amount_max is not None:
            query = query.where(m.amount <= filters.amount_max)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        page = query.order_by(m.date.desc(), m.created_at.desc(), m.id.desc())
        models = await self.session.scalars(page.limit(limit).offset(offset))
        return [_to_domain(model) for model in models], total or 0


def _to_domain(model: TransactionModel) -> Transaction:
    return Transaction(
        id=model.id,
        user_id=model.user_id,
        account_id=model.account_id,
        kind=model.kind,
        amount=model.amount,
        date=model.date,
        category_id=model.category_id,
        description=model.description,
        created_at=model.created_at,
    )
