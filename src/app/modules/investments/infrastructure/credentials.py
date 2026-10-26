"""Tabla y repositorio de las credenciales cifradas de brokers."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    UniqueConstraint,
    delete,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.investments.domain.credentials import Broker, BrokerCredentials, BrokerLink
from app.modules.investments.domain.portfolio import HoldingSnapshot
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository


class BrokerCredentialsModel(UserOwnedMixin, Base):
    __tablename__ = "broker_credentials"
    # Un juego de credenciales por usuario y broker: guardar de nuevo las reemplaza.
    __table_args__ = (UniqueConstraint("user_id", "broker"),)

    broker: Mapped[Broker] = mapped_column(
        Enum(Broker, name="broker", native_enum=False, length=10)
    )
    username_hint: Mapped[str] = mapped_column(String(10))
    # Usuario y contraseña cifrados con Fernet; la clave está en CREDENTIALS_KEY, no acá.
    secret: Mapped[bytes] = mapped_column(LargeBinary)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemyCredentialsRepository(UserScopedRepository[BrokerCredentialsModel]):
    model = BrokerCredentialsModel

    async def save(self, credentials: BrokerCredentials) -> None:
        values = {
            "username_hint": credentials.username_hint,
            "secret": credentials.secret,
            "updated_at": credentials.updated_at,
        }
        upsert = insert(BrokerCredentialsModel).values(
            id=uuid4(), user_id=self.user_id, broker=credentials.broker, **values
        )
        await self.session.execute(
            upsert.on_conflict_do_update(index_elements=["user_id", "broker"], set_=values)
        )

    async def get_credentials(self, broker: Broker) -> BrokerCredentials | None:
        found = await self.session.scalar(
            self.scoped().where(BrokerCredentialsModel.broker == broker)
        )
        if found is None:
            return None
        return BrokerCredentials(
            found.user_id, found.broker, found.username_hint, found.secret, found.updated_at
        )

    async def delete(self, broker: Broker) -> None:
        m = BrokerCredentialsModel
        await self.session.execute(delete(m).where(m.user_id == self.user_id, m.broker == broker))


class BrokerLinkModel(UserOwnedMixin, Base):
    __tablename__ = "broker_links"
    __table_args__ = (UniqueConstraint("user_id", "broker"),)

    broker: Mapped[Broker] = mapped_column(
        Enum(Broker, name="broker", native_enum=False, length=10)
    )
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), index=True)


class SqlAlchemyBrokerLinkRepository(UserScopedRepository[BrokerLinkModel]):
    model = BrokerLinkModel

    async def link(self, link: BrokerLink) -> None:
        upsert = insert(BrokerLinkModel).values(
            id=uuid4(), user_id=self.user_id, broker=link.broker, account_id=link.account_id
        )
        await self.session.execute(
            upsert.on_conflict_do_update(
                index_elements=["user_id", "broker"], set_={"account_id": link.account_id}
            )
        )

    async def linked_account(self, broker: Broker) -> UUID | None:
        query = self.scoped().where(BrokerLinkModel.broker == broker)
        found = await self.session.scalar(query)
        return None if found is None else found.account_id

    async def broker_of(self, account_id: UUID) -> Broker | None:
        query = self.scoped().where(BrokerLinkModel.account_id == account_id)
        found = await self.session.scalar(query)
        return None if found is None else found.broker


class HoldingSnapshotModel(UserOwnedMixin, Base):
    __tablename__ = "holding_snapshots"

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    instrument_id: Mapped[UUID] = mapped_column(ForeignKey("instruments.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8))
    average_price: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    last_price: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemySnapshotRepository(UserScopedRepository[HoldingSnapshotModel]):
    """Cada sincronización reemplaza la foto de la cuenta: acá siempre está la última."""

    model = HoldingSnapshotModel

    async def list_snapshots(self) -> list[HoldingSnapshot]:
        return [
            HoldingSnapshot(
                m.user_id,
                m.account_id,
                m.instrument_id,
                m.quantity,
                m.average_price,
                m.last_price,
                m.taken_at,
                m.id,
            )
            for m in await self.session.scalars(self.scoped())
        ]

    async def replace(self, snapshots: list[HoldingSnapshot]) -> None:
        m = HoldingSnapshotModel
        await self.session.execute(delete(m).where(m.user_id == self.user_id))
        self.session.add_all(
            m(
                id=s.id,
                user_id=self.user_id,
                account_id=s.account_id,
                instrument_id=s.instrument_id,
                quantity=s.quantity,
                average_price=s.average_price,
                last_price=s.last_price,
                taken_at=s.taken_at,
            )
            for s in snapshots
        )
        await self.session.flush()


class BrokerCallsModel(UserOwnedMixin, Base):
    """Llamadas hechas a la API del broker en el mes, contra el cupo de las credenciales."""

    __tablename__ = "broker_calls"
    __table_args__ = (UniqueConstraint("user_id", "broker", "month"),)

    broker: Mapped[Broker] = mapped_column(
        Enum(Broker, name="broker", native_enum=False, length=10)
    )
    # Primer día del mes.
    month: Mapped[date] = mapped_column(Date)
    calls: Mapped[int] = mapped_column(Integer)


class SqlAlchemyCallBudgetRepository(UserScopedRepository[BrokerCallsModel]):
    model = BrokerCallsModel

    async def spend(self, broker: Broker, month: date, calls: int, limit: int) -> bool:
        m = BrokerCallsModel
        # Suma y control en una sola sentencia: dos sincronizaciones a la vez no pasan el tope.
        upsert = insert(m).values(
            id=uuid4(), user_id=self.user_id, broker=broker, month=month, calls=calls
        )
        upsert = upsert.on_conflict_do_update(
            index_elements=["user_id", "broker", "month"],
            set_={"calls": m.calls + calls},
            where=m.calls + calls <= limit,
        )
        return await self.session.scalar(upsert.returning(m.calls)) is not None


async def users_to_sync(session: AsyncSession, broker: Broker) -> list[UUID]:
    """Usuarios con credenciales y una cuenta vinculada a ese broker."""
    link, creds = BrokerLinkModel, BrokerCredentialsModel
    query = (
        select(link.user_id)
        .join(creds, (creds.user_id == link.user_id) & (creds.broker == link.broker))
        .where(link.broker == broker)
    )
    return list(await session.scalars(query))
