"""Tabla, repositorio y Unit of Work de las cuentas del ledger."""

from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from sqlalchemy import DateTime, Enum, Index, Numeric, String, case, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.ledger.domain.account import (
    Account,
    AccountNameTakenError,
    AccountType,
    same_name,
)
from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.infrastructure.transactions import TransactionModel
from app.shared.domain.money import Currency
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository


class AccountModel(UserOwnedMixin, Base):
    __tablename__ = "accounts"
    __table_args__ = (
        # Nombre único por usuario entre las activas, sin distinguir mayúsculas.
        Index(
            "uq_accounts_user_id_active_name",
            "user_id",
            text("lower(name)"),
            unique=True,
            postgresql_where=text("archived_at IS NULL"),
        ),
    )

    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type", native_enum=False, length=20)
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency", native_enum=False, length=3)
    )
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


def _to_domain(model: AccountModel) -> Account:
    return Account(
        id=model.id,
        user_id=model.user_id,
        name=model.name,
        type=model.type,
        currency=model.currency,
        initial_balance=model.initial_balance,
        created_at=model.created_at,
        archived_at=model.archived_at,
    )


class SqlAlchemyAccountRepository(UserScopedRepository[AccountModel]):
    model = AccountModel

    async def name_taken(self, name: str, *, excluding: UUID | None = None) -> bool:
        query = self.scoped().where(
            func.lower(AccountModel.name) == same_name(name), AccountModel.archived_at.is_(None)
        )
        if excluding is not None:
            query = query.where(AccountModel.id != excluding)
        return await self.session.scalar(select(query.exists())) or False

    async def get_account(self, account_id: UUID) -> Account:
        return _to_domain(await self.get(account_id))

    async def list_accounts(self, *, include_archived: bool) -> list[Account]:
        query = self.scoped().order_by(AccountModel.created_at)
        if not include_archived:
            query = query.where(AccountModel.archived_at.is_(None))
        return [_to_domain(model) for model in await self.session.scalars(query)]

    async def save(self, account: Account) -> None:
        try:
            await self.session.execute(
                update(AccountModel)
                .where(AccountModel.id == account.id, AccountModel.user_id == self.user_id)
                .values(
                    name=account.name, currency=account.currency, archived_at=account.archived_at
                )
            )
        except IntegrityError as exc:
            # Dos renombres simultáneos al mismo nombre: los frena el índice único.
            raise AccountNameTakenError from exc

    async def has_movements(self, account_id: UUID) -> bool:
        movements = select(TransactionModel).where(
            TransactionModel.user_id == self.user_id, TransactionModel.account_id == account_id
        )
        return await self.session.scalar(select(movements.exists())) or False

    async def movement_totals(
        self, account_ids: list[UUID], *, as_of: date | None
    ) -> dict[UUID, Decimal]:
        signed = case(
            (TransactionModel.kind == CategoryKind.INCOME, TransactionModel.amount),
            else_=-TransactionModel.amount,
        )
        query = (
            select(TransactionModel.account_id, func.sum(signed))
            .where(
                TransactionModel.user_id == self.user_id,
                TransactionModel.account_id.in_(account_ids),
            )
            .group_by(TransactionModel.account_id)
        )
        if as_of is not None:
            query = query.where(TransactionModel.date <= as_of)
        return dict((await self.session.execute(query)).tuples().all())

    async def add(self, account: Account) -> None:
        self.session.add(
            AccountModel(
                id=account.id,
                user_id=account.user_id,
                name=account.name,
                type=account.type,
                currency=account.currency,
                initial_balance=account.initial_balance,
                created_at=account.created_at,
                archived_at=account.archived_at,
            )
        )
        try:
            await self.session.flush()
        except IntegrityError as exc:
            # Dos altas simultáneas con el mismo nombre: las frena el índice único.
            raise AccountNameTakenError from exc


class SqlAlchemyAccountsUnitOfWork(SqlAlchemyUnitOfWork):
    accounts: SqlAlchemyAccountRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], user_id: UUID) -> None:
        super().__init__(session_factory)
        self._user_id = user_id

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.accounts = SqlAlchemyAccountRepository(self.session, self._user_id)
        return self
