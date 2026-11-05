from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.debts.application.manage_debts import CreateDebt, GetDebt, ListDebts
from app.modules.debts.domain.debt import Debt, DebtDirection, InvalidDebtError
from app.modules.debts.domain.payment import DebtBalance
from app.shared.domain.dates import add_months
from app.shared.domain.money import Currency
from fakes.debts import FakeDebtsUnitOfWork

ANA = uuid4()


def debt(principal: str, n: int, *, rate: str | None = None, fixed: str | None = None) -> Debt:
    return Debt(
        ANA,
        "Banco",
        DebtDirection.OWED,
        Currency.ARS,
        Decimal(principal),
        n,
        date(2027, 1, 31),
        Decimal(rate) if rate else None,
        Decimal(fixed) if fixed else None,
    )


def test_installments_are_monthly_from_a_month_after_the_start() -> None:
    assert [add_months(date(2027, 1, 31), m) for m in (1, 2, 13)] == [
        date(2027, 2, 28),
        date(2027, 3, 31),
        date(2028, 2, 29),
    ]


def test_french_system_has_a_constant_payment_and_repays_the_principal() -> None:
    # 120.000 a 12 meses con TNA 60 %: tasa mensual del 5 %.
    schedule = debt("120000", 12, rate="60").schedule()

    first, last = schedule[0], schedule[-1]
    assert (first.amount, first.interest, first.principal) == (
        Decimal("13539.05"),
        Decimal("6000.00"),
        Decimal("7539.05"),
    )
    assert {i.amount for i in schedule[:-1]} == {Decimal("13539.05")}
    assert abs(last.amount - first.amount) <= Decimal("0.05")
    assert sum(i.principal for i in schedule) == Decimal("120000")


def test_without_rate_the_principal_is_split_and_a_fixed_payment_keeps_its_amount() -> None:
    split = debt("1000", 3).schedule()
    fixed = debt("1000", 3, fixed="400").schedule()

    assert [(i.amount, i.interest) for i in split] == [
        (Decimal("333.34"), Decimal("0.00")),
        (Decimal("333.33"), Decimal("0.00")),
        (Decimal("333.33"), Decimal("0.00")),
    ]
    assert [i.amount for i in fixed] == [Decimal("400")] * 3
    assert sum(i.interest for i in fixed) == Decimal("200.00")


@pytest.mark.parametrize(
    ("principal", "n", "rate", "fixed"),
    [
        ("0", 1, None, None),
        ("100", 0, None, None),
        ("100", 2, "10", "60"),
        ("100", 2, None, "40"),
        ("100", 2, "-1", None),
        ("100", 2, None, "0"),
        ("0.01", 2, None, None),
    ],
)
def test_invalid_debts_are_rejected(
    principal: str, n: int, rate: str | None, fixed: str | None
) -> None:
    with pytest.raises(InvalidDebtError):
        debt(principal, n, rate=rate, fixed=fixed)


async def test_debts_are_saved_with_their_schedule() -> None:
    uow = FakeDebtsUnitOfWork()
    loan = debt("1000", 2)

    created = await CreateDebt(uow)(loan)

    nothing_paid = DebtBalance(Decimal("0.00"), Decimal("1000.00"), 0, created[0])
    assert await ListDebts(uow)() == [(loan, nothing_paid)]
    assert await GetDebt(uow)(loan.id) == (loan, created, nothing_paid)
    assert uow.commits == 1


def test_the_counterparty_is_required() -> None:
    with pytest.raises(InvalidDebtError):
        Debt(ANA, " ", DebtDirection.LENT, Currency.ARS, Decimal("1"), 1, date(2027, 1, 1))
