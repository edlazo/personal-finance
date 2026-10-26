"""Casos de uso: dar de alta, listar y ver tarjetas de crédito."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.modules.cards.domain.card import CreditCard, CreditCardRepository
from app.shared.application.unit_of_work import UnitOfWork


class CardsUnitOfWork(UnitOfWork, Protocol):
    @property
    def cards(self) -> CreditCardRepository: ...


@dataclass(frozen=True)
class CreateCard:
    uow: CardsUnitOfWork

    async def __call__(self, card: CreditCard) -> CreditCard:
        async with self.uow:
            await self.uow.cards.add(card)
            await self.uow.commit()
        return card


@dataclass(frozen=True)
class ListCards:
    uow: CardsUnitOfWork

    async def __call__(self) -> list[CreditCard]:
        async with self.uow:
            return await self.uow.cards.list_cards()


@dataclass(frozen=True)
class GetCard:
    uow: CardsUnitOfWork

    async def __call__(self, card_id: UUID) -> CreditCard:
        async with self.uow:
            return await self.uow.cards.get_card(card_id)
