from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.cards.application.manage_cards import CreateCard, ListCards
from app.modules.cards.domain.card import CardNetwork, CreditCard, InvalidCardError
from app.shared.domain.money import Currency
from fakes.cards import FakeCardsUnitOfWork

ANA = uuid4()


def test_a_card_is_in_pesos_and_also_in_dollars_if_dual_currency() -> None:
    visa = CreditCard(ANA, "  Visa Galicia ", CardNetwork.VISA, 25, 5, dual_currency=True)
    naranja = CreditCard(ANA, "Naranja", CardNetwork.NARANJA, 31, 10, limit=Decimal("500000"))

    assert (visa.name, visa.currencies) == ("Visa Galicia", [Currency.ARS, Currency.USD])
    assert (naranja.currencies, naranja.limit) == ([Currency.ARS], Decimal("500000"))


@pytest.mark.parametrize(
    ("name", "closing", "due", "limit"),
    [(" ", 25, 5, None), ("Visa", 0, 5, None), ("Visa", 25, 32, None), ("Visa", 25, 5, "0")],
)
def test_invalid_cards_are_rejected(name: str, closing: int, due: int, limit: str | None) -> None:
    with pytest.raises(InvalidCardError):
        CreditCard(
            ANA, name, CardNetwork.VISA, closing, due, limit=Decimal(limit) if limit else None
        )


async def test_cards_are_saved_and_listed_by_name() -> None:
    uow = FakeCardsUnitOfWork()
    for name in ("Visa", "Amex"):
        await CreateCard(uow)(CreditCard(ANA, name, CardNetwork.AMEX, 20, 1))

    assert [c.name for c in await ListCards(uow)()] == ["Amex", "Visa"]
    assert uow.commits == 2
