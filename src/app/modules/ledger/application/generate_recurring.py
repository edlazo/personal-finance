"""Casos de uso: generar las ocurrencias vencidas de una regla y resolver las pendientes."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.ledger.application.balance_guard import ensure_non_negative
from app.modules.ledger.application.manage_recurring import RecurringUnitOfWork, check_rule
from app.modules.ledger.domain.recurring import PendingOccurrence
from app.modules.ledger.domain.transaction import Transaction


@dataclass(frozen=True)
class GenerateRecurring:
    """Correrlo dos veces el mismo día no duplica nada: la regla recuerda hasta dónde llegó."""

    uow: RecurringUnitOfWork

    async def __call__(self, rule_id: UUID, today: date) -> int:
        async with self.uow:
            rule = await self.uow.recurring.get_rule(rule_id)
            # Decisión del PO: lo que vence en pausa se saltea.
            dates = [] if rule.paused else rule.due_dates(today)
            if rule.needs_confirmation:
                for day in dates:
                    pending = PendingOccurrence(rule.user_id, rule.id, day, rule.amount)
                    await self.uow.recurring.add_pending(pending)
            elif dates:
                await check_rule(self.uow, rule)
                for day in dates:
                    await self.uow.transactions.add(rule.movement(day))
                await ensure_non_negative(self.uow, {rule.account_id: dates[0]})
            if not await self.uow.recurring.advance(rule, today):
                # Otra corrida ya la procesó: se descarta lo de esta.
                await self.uow.rollback()
                return 0
            await self.uow.commit()
        return len(dates)


@dataclass(frozen=True)
class ListPending:
    uow: RecurringUnitOfWork

    async def __call__(self) -> list[PendingOccurrence]:
        async with self.uow:
            return await self.uow.recurring.list_pending()


@dataclass(frozen=True)
class ConfirmPending:
    uow: RecurringUnitOfWork

    async def __call__(self, pending_id: UUID, amount: Decimal | None = None) -> Transaction:
        """Crea el movimiento con los datos actuales de la regla; el monto se puede ajustar."""
        async with self.uow:
            pending = await self.uow.recurring.get_pending(pending_id)
            rule = await self.uow.recurring.get_rule(pending.rule_id)
            await check_rule(self.uow, rule)
            movement = rule.movement(pending.date, pending.amount if amount is None else amount)
            await self.uow.transactions.add(movement)
            await ensure_non_negative(self.uow, {rule.account_id: pending.date})
            await self.uow.recurring.delete_pending(pending_id)
            await self.uow.commit()
        return movement


@dataclass(frozen=True)
class DiscardPending:
    uow: RecurringUnitOfWork

    async def __call__(self, pending_id: UUID) -> None:
        async with self.uow:
            await self.uow.recurring.get_pending(pending_id)
            await self.uow.recurring.delete_pending(pending_id)
            await self.uow.commit()
