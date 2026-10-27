from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.cards.application.manage_cards import PendingInstallments, RegisterPurchase
from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.modules.cards.domain.purchase import CardPurchase, InvalidPurchaseError
from app.shared.domain.money import Currency
from fakes.cards import FakeCardsUnitOfWork

ANA = uuid4()
VISA = CreditCard(ANA, "Visa", CardNetwork.VISA, closing_day=25, due_day=5)


def buy(amount: str, count: int, on: date, currency: Currency = Currency.ARS) -> CardPurchase:
    return CardPurchase(ANA, VISA.id, "Heladera", Decimal(amount), currency, count, on)


@pytest.mark.parametrize(
    ("closing", "due", "on", "statement"),
    [
        (25, 5, date(2026, 10, 25), (date(2026, 10, 25), date(2026, 11, 5))),
        (25, 5, date(2026, 10, 26), (date(2026, 11, 25), date(2026, 12, 5))),
        (25, 5, date(2026, 12, 30), (date(2027, 1, 25), date(2027, 2, 5))),
        # En un mes más corto, su último día.
        (31, 10, date(2027, 2, 14), (date(2027, 2, 28), date(2027, 3, 10))),
        # Vencimiento posterior al cierre: el mismo mes.
        (5, 15, date(2026, 10, 1), (date(2026, 10, 5), date(2026, 10, 15))),
    ],
)
def test_the_statement_follows_the_closing_day(
    closing: int, due: int, on: date, statement: tuple[date, date]
) -> None:
    card = CreditCard(ANA, "Visa", CardNetwork.VISA, closing, due)

    assert card.statement(on) == statement


def test_installments_go_to_consecutive_statements_and_add_up_to_the_total() -> None:
    first, second, third = buy("1000", 3, date(2026, 11, 30)).schedule(VISA)

    assert [i.amount for i in (first, second, third)] == [
        Decimal("333.34"),
        Decimal("333.33"),
        Decimal("333.33"),
    ]
    assert [(i.number, i.count, i.closing_date) for i in (first, third)] == [
        (1, 3, date(2026, 12, 25)),
        (3, 3, date(2027, 2, 25)),
    ]


def test_dollars_need_a_dual_currency_card() -> None:
    dual = CreditCard(ANA, "Amex", CardNetwork.AMEX, 25, 5, dual_currency=True)
    purchase = buy("50", 1, date(2026, 10, 1), Currency.USD)

    assert [i.currency for i in purchase.schedule(dual)] == [Currency.USD]
    with pytest.raises(InvalidPurchaseError):
        purchase.schedule(VISA)


@pytest.mark.parametrize(("amount", "count"), [("0", 1), ("10.001", 1), ("10", 0), ("0.02", 3)])
def test_invalid_purchases_are_rejected(amount: str, count: int) -> None:
    with pytest.raises(InvalidPurchaseError):
        buy(amount, count, date(2026, 10, 1))


async def test_pending_installments_are_those_not_yet_due() -> None:
    uow = FakeCardsUnitOfWork()
    uow.cards.items.append(VISA)
    await RegisterPurchase(uow)(buy("300", 3, date(2026, 9, 10)))

    pending = await PendingInstallments(uow)(VISA.id, today=date(2026, 10, 6))

    # La 1 venció el 05/10; la 2 cerró el 25/10 y vence el 05/11.
    assert [(i.number, i.due_date) for i in pending] == [
        (2, date(2026, 11, 5)),
        (3, date(2026, 12, 5)),
    ]
