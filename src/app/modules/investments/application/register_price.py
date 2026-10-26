"""Caso de uso: cargar a mano el precio de un instrumento."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.investments.application.list_positions import PositionsUnitOfWork
from app.modules.investments.domain.price import InstrumentPrice


@dataclass(frozen=True)
class RegisterPrice:
    uow: PositionsUnitOfWork

    async def __call__(
        self, user_id: UUID, *, instrument_id: UUID, price: Decimal, on: date
    ) -> InstrumentPrice:
        entry = InstrumentPrice(user_id, instrument_id, price, on)
        async with self.uow:
            # 404 si el instrumento no existe o es de otro usuario.
            await self.uow.instruments.get_instrument(instrument_id)
            await self.uow.prices.add(entry)
            await self.uow.commit()
        return entry
