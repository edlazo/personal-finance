from datetime import date
from types import TracebackType
from typing import Self
from uuid import UUID

from app.modules.cards.domain.card import CreditCard
from app.modules.cards.domain.purchase import CardPurchase, Installment
from app.shared.domain.errors import NotFoundError


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

    async def pending_installments(self, card_id: UUID, today: date) -> list[Installment]:
        rows = [(p, i) for c, p, i in self.installments if c == card_id and i.due_date >= today]
        return [i for _, i in sorted(rows, key=lambda r: (r[1].due_date, r[0].date, r[1].number))]


class FakeCardsUnitOfWork:
    def __init__(self) -> None:
        self.cards = InMemoryCards()
        self.purchases = InMemoryPurchases()
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
