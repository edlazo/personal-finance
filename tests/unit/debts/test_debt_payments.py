from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.debts.application.manage_debts import CreateDebt, GetDebt, RegisterDebtPayment
from app.modules.debts.domain.debt import Debt, DebtDirection
from app.modules.debts.domain.payment import DebtPayment, InvalidPaymentError
from app.shared.domain.cash import CashAccount
from app.shared.domain.money import Currency
from fakes.debts import FakeDebtsUnitOfWork

ANA = uuid4()


async def pay(
    direction: DebtDirection, amount: str, currency: Currency = Currency.ARS, archived: bool = False
) -> tuple[FakeDebtsUnitOfWork, Debt, CashAccount]:
    """Paga una deuda de 3000 en pesos, en 3 cuotas de 1000, desde una cuenta nueva."""
    uow = FakeDebtsUnitOfWork()
    debt = Debt(ANA, "Juan", direction, Currency.ARS, Decimal("3000"), 3, date(2027, 1, 10))
    await CreateDebt(uow)(debt)
    account = CashAccount(uuid4(), currency, holds_investments=False, archived=archived)
    uow.cash.accounts[account.id] = account
    payment = DebtPayment(ANA, debt.id, account.id, Decimal(amount), date(2027, 2, 10))
    await RegisterDebtPayment(uow)(payment)
    return uow, debt, account


async def test_collecting_a_loan_credits_the_account_until_it_is_settled() -> None:
    uow, loan, account = await pay(DebtDirection.LENT, "3000")
    _, _, balance = await GetDebt(uow)(loan.id)

    assert (balance.pending, balance.paid_installments, balance.next_installment) == (
        Decimal("0.00"),
        3,
        None,
    )
    assert uow.cash.recorded == [(account.id, Decimal("3000"), True)]


@pytest.mark.parametrize(
    ("amount", "currency", "archived"),
    [("3000.01", Currency.ARS, False), ("100", Currency.USD, False), ("100", Currency.ARS, True)],
)
async def test_invalid_payments_are_rejected(
    amount: str, currency: Currency, archived: bool
) -> None:
    with pytest.raises(InvalidPaymentError):
        await pay(DebtDirection.OWED, amount, currency, archived)
