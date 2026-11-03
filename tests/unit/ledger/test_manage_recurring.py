from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.ledger.application.generate_recurring import (
    ConfirmPending,
    DiscardPending,
    GenerateRecurring,
    ListPending,
)
from app.modules.ledger.application.manage_recurring import (
    CreateRecurring,
    DeleteRecurring,
    ListRecurring,
    UpdateRecurring,
)
from app.modules.ledger.domain.account import Account, AccountType, NegativeBalanceError
from app.modules.ledger.domain.category import Category, CategoryKind
from app.modules.ledger.domain.recurring import Frequency, InvalidRecurringError, RecurringRule
from app.modules.ledger.domain.transaction import InvalidTransactionError
from app.shared.domain.errors import NotFoundError
from app.shared.domain.money import Currency
from fakes.ledger import FakeLedgerUnitOfWork

USER = uuid4()
EXPENSE = CategoryKind.EXPENSE


def setup() -> tuple[FakeLedgerUnitOfWork, Account, Category]:
    uow = FakeLedgerUnitOfWork()
    account = Account(USER, "Galicia", AccountType.SAVINGS, Currency.ARS, Decimal("0"))
    rent = Category(USER, "Alquiler", EXPENSE)
    uow.accounts.items[account.id] = account
    uow.categories.items[rent.id] = rent
    return uow, account, rent


def rule(account: Account, category: Category, **changes: object) -> RecurringRule:
    values: dict[str, object] = {
        "kind": EXPENSE,
        "amount": Decimal("500000"),
        "frequency": Frequency.MONTHLY,
        "start_date": date(2026, 11, 10),
    } | changes
    return RecurringRule(USER, account.id, category_id=category.id, **values)  # type: ignore[arg-type]


async def test_a_rule_is_created_edited_paused_and_deleted() -> None:
    uow, account, rent = setup()
    created = await CreateRecurring(uow)(rule(account, rent, end_date=date(2027, 10, 10)))
    update = UpdateRecurring(uow)

    edited = await update(created.id, {"amount": Decimal("550000"), "end_date": None})
    paused = await update(created.id, {"paused": True})
    resumed = await update(created.id, {"paused": False})

    assert (edited.amount, edited.end_date) == (Decimal("550000"), None)
    assert (paused.paused, resumed.paused) == (True, False)
    assert await ListRecurring(uow)() == [resumed]
    await DeleteRecurring(uow)(created.id)
    assert await ListRecurring(uow)() == []
    with pytest.raises(NotFoundError):
        await DeleteRecurring(uow)(created.id)


async def test_a_rule_is_checked_like_a_movement() -> None:
    uow, account, rent = setup()
    created = await CreateRecurring(uow)(rule(account, rent))
    account.archived_at = datetime.now(UTC)

    with pytest.raises(InvalidTransactionError):
        await CreateRecurring(uow)(rule(account, rent, kind=CategoryKind.INCOME))
    with pytest.raises(InvalidTransactionError):
        await CreateRecurring(uow)(rule(account, rent))
    with pytest.raises(InvalidTransactionError):
        await UpdateRecurring(uow)(created.id, {"kind": CategoryKind.INCOME})
    # Pausar no vuelve a validar la cuenta, aunque esté archivada.
    assert (await UpdateRecurring(uow)(created.id, {"paused": True})).paused


@pytest.mark.parametrize(
    "changes",
    [{"amount": Decimal("0")}, {"amount": Decimal("1.001")}, {"end_date": date(2026, 11, 9)}],
)
async def test_invalid_rules_are_rejected(changes: dict[str, object]) -> None:
    uow, account, rent = setup()
    created = await CreateRecurring(uow)(rule(account, rent))

    with pytest.raises(InvalidRecurringError):
        rule(account, rent, **changes)
    with pytest.raises(InvalidRecurringError):
        await UpdateRecurring(uow)(created.id, changes)


def test_occurrences_keep_the_start_day_and_respect_the_end() -> None:
    _, account, rent = setup()
    monthly = rule(account, rent, start_date=date(2027, 1, 31), end_date=date(2027, 3, 31))
    yearly = rule(account, rent, frequency=Frequency.YEARLY, start_date=date(2028, 2, 29))
    weekly = rule(account, rent, frequency=Frequency.WEEKLY, generated_until=date(2026, 11, 17))

    # Un mes corto no corre el día de los siguientes.
    assert monthly.due_dates(date(2027, 12, 31)) == [
        date(2027, 1, 31),
        date(2027, 2, 28),
        date(2027, 3, 31),
    ]
    assert yearly.due_dates(date(2029, 3, 1)) == [date(2028, 2, 29), date(2029, 2, 28)]
    assert weekly.due_dates(date(2026, 12, 1)) == [date(2026, 11, 24), date(2026, 12, 1)]
    assert weekly.due_dates(date(2026, 11, 9)) == []


async def test_due_movements_are_generated_once_and_pauses_skip() -> None:
    uow, account, rent = setup()
    account.initial_balance = Decimal("2000000")
    created = await CreateRecurring(uow)(rule(account, rent, start_date=date(2026, 9, 10)))
    generate = GenerateRecurring(uow)

    assert await generate(created.id, date(2026, 11, 20)) == 3
    assert await generate(created.id, date(2026, 11, 20)) == 0
    await UpdateRecurring(uow)(created.id, {"paused": True})
    assert await generate(created.id, date(2026, 12, 20)) == 0
    await UpdateRecurring(uow)(created.id, {"paused": False})
    assert await generate(created.id, date(2027, 1, 10)) == 1

    days = sorted(t.date for t in uow.transactions.items)
    assert days == [date(2026, 9, 10), date(2026, 10, 10), date(2026, 11, 10), date(2027, 1, 10)]
    assert {(t.amount, t.category_id) for t in uow.transactions.items} == {
        (Decimal("500000"), rent.id)
    }


async def test_a_failed_generation_keeps_the_rule_behind() -> None:
    uow, account, rent = setup()
    created = await CreateRecurring(uow)(rule(account, rent))

    with pytest.raises(NegativeBalanceError):
        await GenerateRecurring(uow)(created.id, date(2026, 11, 10))

    assert uow.transactions.items == []
    assert (await uow.recurring.get_rule(created.id)).generated_until is None


async def test_another_run_that_got_there_first_wins() -> None:
    uow, account, rent = setup()
    account.initial_balance = Decimal("2000000")
    created = await CreateRecurring(uow)(rule(account, rent))

    async def taken(rule: RecurringRule, until: date) -> bool:
        return False

    uow.recurring.advance = taken  # type: ignore[method-assign]
    assert await GenerateRecurring(uow)(created.id, date(2026, 11, 10)) == 0
    assert uow.commits == 1


async def test_pending_occurrences_are_confirmed_or_discarded() -> None:
    uow, account, rent = setup()
    account.initial_balance = Decimal("2000000")
    created = await CreateRecurring(uow)(
        rule(account, rent, start_date=date(2026, 9, 10), needs_confirmation=True)
    )

    assert await GenerateRecurring(uow)(created.id, date(2026, 10, 10)) == 2
    assert uow.transactions.items == []
    first, second = await ListPending(uow)()

    confirmed = await ConfirmPending(uow)(first.id, Decimal("480000"))
    await DiscardPending(uow)(second.id)

    assert (confirmed.date, confirmed.amount) == (date(2026, 9, 10), Decimal("480000"))
    assert uow.transactions.items == [confirmed]
    assert await ListPending(uow)() == []
    with pytest.raises(NotFoundError):
        await ConfirmPending(uow)(second.id)
