from types import TracebackType
from typing import Self
from uuid import UUID

from app.modules.cards.domain.card import CreditCard
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


class FakeCardsUnitOfWork:
    def __init__(self) -> None:
        self.cards = InMemoryCards()
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
