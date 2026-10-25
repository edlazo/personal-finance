from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.ledger.application.manage_accounts import (
    ArchiveAccount,
    GetAccount,
    ListAccounts,
    UpdateAccount,
)
from app.modules.ledger.domain.account import (
    Account,
    AccountArchivedError,
    AccountNameTakenError,
    AccountType,
)
from app.shared.domain.errors import NotFoundError
from app.shared.domain.money import Currency
from fakes.accounts import FakeAccountsUnitOfWork

USER = uuid4()


@pytest.fixture
def uow() -> FakeAccountsUnitOfWork:
    return FakeAccountsUnitOfWork()


def add(uow: FakeAccountsUnitOfWork, name: str) -> Account:
    account = Account(USER, name, AccountType.SAVINGS, Currency.ARS, Decimal("0"))
    uow.accounts.items[account.id] = account
    return account


async def test_edit_name_and_currency_allowing_a_case_change_of_its_own_name(
    uow: FakeAccountsUnitOfWork,
) -> None:
    galicia = add(uow, "galicia")

    edited = await UpdateAccount(uow=uow)(galicia.id, name=" Galicia ", currency=Currency.USD)

    assert (edited.name, edited.currency) == ("Galicia", Currency.USD)
    assert uow.committed


async def test_edit_rejects_the_name_of_another_active_account(
    uow: FakeAccountsUnitOfWork,
) -> None:
    add(uow, "Galicia")
    santander = add(uow, "Santander")

    with pytest.raises(AccountNameTakenError):
        await UpdateAccount(uow=uow)(santander.id, name="GALICIA")


async def test_archived_accounts_are_read_only_and_archiving_twice_is_fine(
    uow: FakeAccountsUnitOfWork,
) -> None:
    galicia = add(uow, "Galicia")
    archive = ArchiveAccount(uow=uow)
    await archive(galicia.id)
    first_archived_at = galicia.archived_at
    await archive(galicia.id)

    assert galicia.archived_at == first_archived_at
    with pytest.raises(AccountArchivedError):
        await UpdateAccount(uow=uow)(galicia.id, name="Otra")


async def test_list_hides_archived_unless_asked(uow: FakeAccountsUnitOfWork) -> None:
    add(uow, "Galicia")
    add(uow, "Viejo banco").archive()

    assert [a.account.name for a in await ListAccounts(uow=uow)()] == ["Galicia"]
    assert len(await ListAccounts(uow=uow)(include_archived=True)) == 2


async def test_unknown_account_is_not_found(uow: FakeAccountsUnitOfWork) -> None:
    with pytest.raises(NotFoundError):
        await ArchiveAccount(uow=uow)(uuid4())


async def test_balance_is_the_initial_balance_plus_movements(uow: FakeAccountsUnitOfWork) -> None:
    galicia = Account(USER, "Galicia", AccountType.SAVINGS, Currency.ARS, Decimal("1000.00"))
    efectivo = add(uow, "Efectivo")
    uow.accounts.items[galicia.id] = galicia
    uow.accounts.totals[galicia.id] = Decimal("299.50")

    balances = {a.account.name: a.balance for a in await ListAccounts(uow=uow)()}

    assert balances == {"Galicia": Decimal("1299.50"), "Efectivo": Decimal("0")}
    assert (await GetAccount(uow=uow)(efectivo.id)).balance == Decimal("0")
