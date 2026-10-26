"""Tabla y repositorio de las credenciales cifradas de brokers."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Enum, LargeBinary, String, UniqueConstraint, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.investments.domain.credentials import Broker, BrokerCredentials
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
