from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.cards.application.manage_cards import (
    GetStatement,
    RegisterPayment,
    RegisterPurchase,
)
from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.modules.cards.domain.payment import CardPayment, InvalidPaymentError
from app.modules.cards.domain.purchase import CardPurchase
from app.shared.domain.cash import CashAccount
from app.shared.domain.money import Currency
from fakes.cards import FakeCardsUnitOfWork

ANA = uuid4()
VISA = CreditCard(ANA, "Visa", CardNetwork.VISA, closing_day=25, due_day=5)
PESOS = CashAccount(uuid4(), Currency.ARS, holds_investments=False, archived=False)
DOLLARS = CashAccount(uuid4(), Currency.USD, holds_investments=False, archived=False)
OLD = CashAccount(uuid4(), Currency.ARS, holds_investments=False, archived=True)


async def card_with_a_purchase() -> FakeCardsUnitOfWork:
    uow = FakeCardsUnitOfWork()
    uow.cards.items.append(VISA)
    uow.cash.accounts.update({a.id: a for a in (PESOS, DOLLARS, OLD)})
    tv = CardPurchase(ANA, VISA.id, "Tele", Decimal("1000"), Currency.ARS, 2, date(2026, 10, 20))
    await RegisterPurchase(uow)(tv)
    return uow


async def pay(
    uow: FakeCardsUnitOfWork, account: CashAccount, amount: str, currency: Currency = Currency.ARS
) -> CardPayment:
    on, value = date(2026, 11, 2), Decimal(amount)
    register = RegisterPayment(uow)
    return await register(
        ANA, VISA.id, 2026, 10, account_id=account.id, amount=value, currency=currency, on=on
    )


async def test_a_partial_payment_leaves_the_rest_pending_and_moves_the_account() -> None:
    uow = await card_with_a_purchase()

    payment = await pay(uow, PESOS, "300")
    october = await GetStatement(uow)(VISA.id, 2026, 10)

    assert payment.closing_date == date(2026, 10, 25)
    assert (october.total(Currency.ARS), october.pending(Currency.ARS)) == (
        Decimal("500.00"),
        Decimal("200.00"),
    )
    assert uow.cash.recorded == [(PESOS.id, Decimal("300"), False)]


@pytest.mark.parametrize(
    ("account", "amount", "currency"),
    [
        (PESOS, "0", Currency.ARS),  # monto inválido
        (PESOS, "500.01", Currency.ARS),  # más de lo que falta pagar
        (DOLLARS, "100", Currency.ARS),  # cuenta en otra moneda
        (OLD, "100", Currency.ARS),  # cuenta archivada
        (DOLLARS, "1", Currency.USD),  # sin saldo en dólares
    ],
)
async def test_invalid_payments_are_rejected(
    account: CashAccount, amount: str, currency: Currency
) -> None:
    uow = await card_with_a_purchase()

    with pytest.raises(InvalidPaymentError):
        await pay(uow, account, amount, currency)
    assert (uow.payments.items, uow.cash.recorded) == ([], [])
