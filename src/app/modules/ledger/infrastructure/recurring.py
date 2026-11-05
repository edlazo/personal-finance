"""Tabla y repositorio de las reglas de movimientos recurrentes."""

from dataclasses import fields
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    delete,
    select,
    update,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.recurring import Frequency, PendingOccurrence, RecurringRule
from app.shared.domain.errors import NotFoundError
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository


class RecurringRuleModel(UserOwnedMixin, Base):
    __tablename__ = "recurring_rules"

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id"))
    kind: Mapped[CategoryKind] = mapped_column(
        Enum(CategoryKind, name="transaction_kind", native_enum=False, length=10)
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    frequency: Mapped[Frequency] = mapped_column(
        Enum(Frequency, name="recurring_frequency", native_enum=False, length=10)
    )
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(String(200))
    paused: Mapped[bool] = mapped_column(Boolean)
    needs_confirmation: Mapped[bool] = mapped_column(Boolean, server_default="false")
    generated_until: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PendingOccurrenceModel(UserOwnedMixin, Base):
    __tablename__ = "recurring_pending"
    # Una sola pendiente por regla y fecha, aunque el job corra dos veces.
    __table_args__ = (UniqueConstraint("rule_id", "date"),)

    # Si se borra la regla, se van sus pendientes.
    rule_id: Mapped[UUID] = mapped_column(ForeignKey("recurring_rules.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))


# Los campos de la regla que van en columnas propias, salvo id, usuario y alta.
FIELDS = [f.name for f in fields(RecurringRule) if f.name not in {"user_id", "id", "created_at"}]
# generated_until lo mueve solo el job, con advance(): una edición no lo pisa.
EDITABLE = [f for f in FIELDS if f != "generated_until"]


def _to_domain(m: RecurringRuleModel) -> RecurringRule:
    return RecurringRule(
        m.user_id, **{f: getattr(m, f) for f in FIELDS}, id=m.id, created_at=m.created_at
    )


class SqlAlchemyRecurringRuleRepository(UserScopedRepository[RecurringRuleModel]):
    model = RecurringRuleModel

    async def add(self, rule: RecurringRule) -> None:
        values = {f: getattr(rule, f) for f in FIELDS}
        self.session.add(
            RecurringRuleModel(
                id=rule.id, user_id=rule.user_id, created_at=rule.created_at, **values
            )
        )
        await self.session.flush()

    async def list_rules(self) -> list[RecurringRule]:
        query = self.scoped().order_by(RecurringRuleModel.start_date, RecurringRuleModel.created_at)
        return [_to_domain(m) for m in await self.session.scalars(query)]

    async def get_rule(self, rule_id: UUID) -> RecurringRule:
        return _to_domain(await self.get(rule_id))

    async def save(self, rule: RecurringRule) -> None:
        model = await self.get(rule.id)
        for f in EDITABLE:
            setattr(model, f, getattr(rule, f))
        await self.session.flush()

    async def delete(self, rule_id: UUID) -> None:
        m = RecurringRuleModel
        await self.session.execute(delete(m).where(m.user_id == self.user_id, m.id == rule_id))

    async def advance(self, rule: RecurringRule, until: date) -> bool:
        m = RecurringRuleModel
        moved = await self.session.scalar(
            update(m)
            .where(
                m.user_id == self.user_id,
                m.id == rule.id,
                m.generated_until.is_not_distinct_from(rule.generated_until),
            )
            .values(generated_until=until)
            .returning(m.id)
        )
        return moved is not None

    async def add_pending(self, pending: PendingOccurrence) -> None:
        self.session.add(PendingOccurrenceModel(**vars(pending)))
        await self.session.flush()

    async def list_pending(self) -> list[PendingOccurrence]:
        m = PendingOccurrenceModel
        query = select(m).where(m.user_id == self.user_id).order_by(m.date, m.id)
        return [_pending(p) for p in await self.session.scalars(query)]

    async def get_pending(self, pending_id: UUID) -> PendingOccurrence:
        m = PendingOccurrenceModel
        found = await self.session.scalar(
            select(m).where(m.user_id == self.user_id, m.id == pending_id)
        )
        if found is None:
            raise NotFoundError("El recurso no existe")
        return _pending(found)

    async def delete_pending(self, pending_id: UUID) -> None:
        m = PendingOccurrenceModel
        await self.session.execute(delete(m).where(m.user_id == self.user_id, m.id == pending_id))


def _pending(m: PendingOccurrenceModel) -> PendingOccurrence:
    return PendingOccurrence(m.user_id, m.rule_id, m.date, m.amount, m.id)
