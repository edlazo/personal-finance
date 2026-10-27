"""Casos de uso: tarjetas de crédito y sus compras en cuotas."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from app.modules.cards.domain.card import CreditCard, CreditCardRepository
from app.modules.cards.domain.purchase import CardPurchase, Installment, PurchaseRepository
from app.shared.application.unit_of_work import UnitOfWork


class CardsUnitOfWork(UnitOfWork, Protocol):
    @property
    def cards(self) -> CreditCardRepository: ...

    @property
    def purchases(self) -> PurchaseRepository: ...


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


@dataclass(frozen=True)
class RegisterPurchase:
    uow: CardsUnitOfWork

    async def __call__(self, purchase: CardPurchase) -> list[Installment]:
        async with self.uow:
            card = await self.uow.cards.get_card(purchase.card_id)
            installments = purchase.schedule(card)
            await self.uow.purchases.add(purchase, installments)
            await self.uow.commit()
        return installments


@dataclass(frozen=True)
class PendingInstallments:
    uow: CardsUnitOfWork

    async def __call__(self, card_id: UUID, today: date) -> list[Installment]:
        async with self.uow:
            # 404 si la tarjeta no existe o es de otro usuario.
            await self.uow.cards.get_card(card_id)
            return await self.uow.purchases.pending_installments(card_id, today)
