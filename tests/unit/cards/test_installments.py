from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.cards.application.manage_cards import (
    GetStatement,
    PendingInstallments,
    RegisterPurchase,
)
from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.modules.cards.domain.payment import CardPayment
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


async def test_pending_installments_are_those_of_statements_not_fully_paid() -> None:
    uow = FakeCardsUnitOfWork()
    uow.cards.items.append(VISA)
    await RegisterPurchase(uow)(buy("300", 3, date(2026, 9, 10)))
    for closing, amount in ((date(2026, 9, 25), "100"), (date(2026, 10, 25), "50")):
        await uow.payments.add(
            CardPayment(
                ANA, VISA.id, uuid4(), closing, Decimal(amount), Currency.ARS, date(2026, 10, 1)
            )
        )

    pending = await PendingInstallments(uow)(VISA.id)

    # La 1 está pagada; la 2, solo en parte; la 3, nada.
    assert [i.number for i in pending] == [2, 3]


async def test_the_statement_of_a_month_has_its_items_and_totals_per_currency() -> None:
    uow = FakeCardsUnitOfWork()
    amex = CreditCard(ANA, "Amex", CardNetwork.AMEX, 25, 5, dual_currency=True)
    uow.cards.items.append(amex)
    for amount, count, on, currency in (
        ("1000", 3, date(2026, 10, 20), Currency.ARS),
        ("12.99", 1, date(2026, 11, 3), Currency.USD),
    ):
        purchase = CardPurchase(ANA, amex.id, "Compra", Decimal(amount), currency, count, on)
        await RegisterPurchase(uow)(purchase)

    november = await GetStatement(uow)(amex.id, 2026, 11)
    empty = await GetStatement(uow)(amex.id, 2027, 5)

    assert (november.closing_date, november.due_date) == (date(2026, 11, 25), date(2026, 12, 5))
    assert [(i.number, i.count, i.purchase_date) for i in november.items] == [
        (2, 3, date(2026, 10, 20)),
        (1, 1, date(2026, 11, 3)),
    ]
    assert (november.total(Currency.ARS), november.total(Currency.USD)) == (
        Decimal("333.33"),
        Decimal("12.99"),
    )
    assert (empty.items, empty.total(Currency.ARS), empty.closing_date) == (
        [],
        Decimal("0.00"),
        date(2027, 5, 25),
    )
