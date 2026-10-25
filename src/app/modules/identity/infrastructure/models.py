"""Tablas de identity."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.domain.rates import RateType
from app.shared.infrastructure.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    # Se guarda normalizado (minúsculas): el índice único alcanza para evitar duplicados.
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    default_rate_type: Mapped[RateType] = mapped_column(
        Enum(RateType, name="rate_type", native_enum=False, create_constraint=True, length=10)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
