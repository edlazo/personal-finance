"""Casos de uso: alta, consulta, edición (pausar o reanudar incluido) y baja de recurrentes."""

from dataclasses import dataclass, replace
from typing import Any, Protocol
from uuid import UUID

from app.modules.ledger.application.create_transaction import TransactionsUnitOfWork
from app.modules.ledger.domain.recurring import RecurringRule, RecurringRuleRepository
from app.modules.ledger.domain.transaction import check_movement

# Si cambia alguno, se vuelve a validar como un movimiento nuevo.
MOVEMENT_FIELDS = {"account_id", "kind", "category_id"}


class RecurringUnitOfWork(TransactionsUnitOfWork, Protocol):
    @property
    def recurring(self) -> RecurringRuleRepository: ...


async def check_rule(uow: RecurringUnitOfWork, rule: RecurringRule) -> None:
    account = await uow.accounts.get_account(rule.account_id)
    check_movement(rule.kind, account, await uow.categories.get_category(rule.category_id))


@dataclass(frozen=True)
class CreateRecurring:
    uow: RecurringUnitOfWork

    async def __call__(self, rule: RecurringRule) -> RecurringRule:
        async with self.uow:
            await check_rule(self.uow, rule)
            await self.uow.recurring.add(rule)
            await self.uow.commit()
        return rule


@dataclass(frozen=True)
class ListRecurring:
    uow: RecurringUnitOfWork

    async def __call__(self) -> list[RecurringRule]:
        async with self.uow:
            return await self.uow.recurring.list_rules()


@dataclass(frozen=True)
class GetRecurring:
    uow: RecurringUnitOfWork

    async def __call__(self, rule_id: UUID) -> RecurringRule:
        async with self.uow:
            return await self.uow.recurring.get_rule(rule_id)


@dataclass(frozen=True)
class UpdateRecurring:
    uow: RecurringUnitOfWork

    async def __call__(self, rule_id: UUID, changes: dict[str, Any]) -> RecurringRule:
        """Cambia solo los campos recibidos; `paused` pausa o reanuda la regla."""
        async with self.uow:
            # replace() vuelve a validar el monto y las fechas.
            rule = replace(await self.uow.recurring.get_rule(rule_id), **changes)
            if MOVEMENT_FIELDS & changes.keys():
                await check_rule(self.uow, rule)
            await self.uow.recurring.save(rule)
            await self.uow.commit()
        return rule


@dataclass(frozen=True)
class DeleteRecurring:
    uow: RecurringUnitOfWork

    async def __call__(self, rule_id: UUID) -> None:
        async with self.uow:
            await self.uow.recurring.get_rule(rule_id)
            await self.uow.recurring.delete(rule_id)
            await self.uow.commit()
