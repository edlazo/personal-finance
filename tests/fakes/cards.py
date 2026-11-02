from datetime import date
from decimal import Decimal
from types import TracebackType
from typing import Self
from uuid import UUID

from app.modules.cards.domain.card import CreditCard
from app.modules.cards.domain.payment import CardPayment
from app.modules.cards.domain.purchase import CardPurchase, Installment
from app.shared.domain.errors import NotFoundError
from app.shared.domain.money import Currency
from fakes.investments import FakeCash


class InMemoryCards:
    def __init__(self) -> None:
        self.items: list[CreditCard] = []

    async def add(self, card: CreditCard) -> None:
        self.items.append(card)

    async def list_cards(self) -> list[CreditCard]:
        return sorted(self.items, key=lambda c: c.name)

    async def get_card(self, card_id: UUID) -> CreditCard:
        found = next((c for c in self.items if c.id == card_id), None)
        if found is None:
            raise NotFoundError("El recurso no existe")
        return found


class InMemoryPurchases:
    def __init__(self) -> None:
        self.installments: list[tuple[UUID, CardPurchase, Installment]] = []

    async def add(self, purchase: CardPurchase, installments: list[Installment]) -> None:
        self.installments += [(purchase.card_id, purchase, i) for i in installments]

    async def card_installments(self, card_id: UUID) -> list[Installment]:
        rows = [(p, i) for c, p, i in self.installments if c == card_id]
        return [i for _, i in sorted(rows, key=lambda r: (r[1].due_date, r[0].date, r[1].number))]

    async def statement_installments(self, card_id: UUID, closing_date: date) -> list[Installment]:
        rows = [
            i for c, _, i in self.installments if c == card_id and i.closing_date == closing_date
        ]
        return sorted(rows, key=lambda i: (i.purchase_date, i.number))


class InMemoryPayments:
    def __init__(self) -> None:
        self.items: list[CardPayment] = []

    async def add(self, payment: CardPayment) -> None:
        self.items.append(payment)

    async def paid(self, card_id: UUID) -> dict[tuple[date, Currency], Decimal]:
        totals: dict[tuple[date, Currency], Decimal] = {}
        for p in (p for p in self.items if p.card_id == card_id):
            key = (p.closing_date, p.currency)
            totals[key] = totals.get(key, Decimal("0")) + p.amount
        return totals


class FakeCardsUnitOfWork:
    def __init__(self) -> None:
        self.cards = InMemoryCards()
        self.purchases = InMemoryPurchases()
        self.payments = InMemoryPayments()
        self.cash = FakeCash()
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass
