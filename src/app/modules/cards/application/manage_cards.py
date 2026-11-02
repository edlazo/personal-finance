"""Casos de uso: tarjetas de crédito y sus compras en cuotas."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.cards.domain.card import CreditCard, CreditCardRepository
from app.modules.cards.domain.payment import CardPayment, InvalidPaymentError, PaymentRepository
from app.modules.cards.domain.purchase import (
    CardPurchase,
    Installment,
    PurchaseRepository,
    Statement,
)
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.cash import CashMovements
from app.shared.domain.money import Currency


class CardsUnitOfWork(UnitOfWork, Protocol):
    @property
    def cards(self) -> CreditCardRepository: ...

    @property
    def purchases(self) -> PurchaseRepository: ...

    @property
    def payments(self) -> PaymentRepository: ...

    @property
    def cash(self) -> CashMovements: ...


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

    async def __call__(self, card_id: UUID) -> list[Installment]:
        """Decisión del PO: las cuotas de resúmenes que no están pagados completos en su moneda,
        aunque ya hayan vencido."""
        async with self.uow:
            # 404 si la tarjeta no existe o es de otro usuario.
            await self.uow.cards.get_card(card_id)
            installments = await self.uow.purchases.card_installments(card_id)
            paid = await self.uow.payments.paid(card_id)
        owed: defaultdict[tuple[date, Currency], Decimal] = defaultdict(Decimal)
        for i in installments:
            owed[(i.closing_date, i.currency)] += i.amount
        return [
            i
            for i in installments
            if paid.get((i.closing_date, i.currency), 0) < owed[(i.closing_date, i.currency)]
        ]


async def _statement(uow: CardsUnitOfWork, card: CreditCard, year: int, month: int) -> Statement:
    # Una compra del día 1 entra en el resumen que cierra ese mes.
    closing, due = card.statement(date(year, month, 1))
    items = await uow.purchases.statement_installments(card.id, closing)
    paid = {
        currency: amount
        for (on, currency), amount in (await uow.payments.paid(card.id)).items()
        if on == closing
    }
    return Statement(closing, due, items, paid)


@dataclass(frozen=True)
class GetStatement:
    uow: CardsUnitOfWork

    async def __call__(self, card_id: UUID, year: int, month: int) -> Statement:
        """El resumen que cierra en ese mes, aunque no tenga consumos."""
        async with self.uow:
            card = await self.uow.cards.get_card(card_id)
            return await _statement(self.uow, card, year, month)


@dataclass(frozen=True)
class RegisterPayment:
    uow: CardsUnitOfWork

    async def __call__(
        self,
        user_id: UUID,
        card_id: UUID,
        year: int,
        month: int,
        *,
        account_id: UUID,
        amount: Decimal,
        currency: Currency,
        on: date,
    ) -> CardPayment:
        async with self.uow:
            card = await self.uow.cards.get_card(card_id)
            statement = await _statement(self.uow, card, year, month)
            payment = CardPayment(
                user_id, card_id, account_id, statement.closing_date, amount, currency, on
            )
            # Decisión del PO: cada moneda se paga desde una cuenta en esa moneda.
            account = await self.uow.cash.account(account_id)
            if account.archived or account.currency is not currency:
                raise InvalidPaymentError(f"Se paga desde una cuenta activa en {currency}")
            pending = statement.pending(currency)
            if amount > pending:
                raise InvalidPaymentError(f"Del resumen falta pagar {pending} {currency}")
            await self.uow.payments.add(payment)
            # Salida sin categoría ligada al pago, como las operaciones de inversión: no es un
            # gasto (lo son las compras) y no puede dejar la cuenta en negativo.
            await self.uow.cash.record_trade(
                account_id,
                amount,
                incoming=False,
                on=on,
                trade_id=payment.id,
                description=f"Pago del resumen de {card.name}",
            )
            await self.uow.commit()
        return payment
