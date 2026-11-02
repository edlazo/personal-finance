from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.ledger.application.manage_recurring import (
    CreateRecurring,
    DeleteRecurring,
    ListRecurring,
    UpdateRecurring,
)
from app.modules.ledger.domain.account import Account, AccountType
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
