"""Tabla, repositorio y Unit of Work de cuentas."""

from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from sqlalchemy import DateTime, Enum, Index, Numeric, String, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.accounts.domain.account import (
    Account,
    AccountNameTakenError,
    AccountType,
    same_name,
)
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


class SqlAlchemyAccountRepository(UserScopedRepository[AccountModel]):
    model = AccountModel

    async def name_taken(self, name: str) -> bool:
        query = self.scoped().where(
            func.lower(AccountModel.name) == same_name(name), AccountModel.archived_at.is_(None)
        )
        return await self.session.scalar(select(query.exists())) or False

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
