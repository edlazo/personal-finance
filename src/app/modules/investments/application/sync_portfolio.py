"""Caso de uso: traer el portafolio de IOL de un usuario y guardar la foto."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.investments.domain.credentials import (
    Broker,
    BrokerLinkRepository,
    CredentialCipher,
    CredentialsRepository,
)
from app.modules.investments.domain.instrument import Instrument, InstrumentRepository
from app.modules.investments.domain.portfolio import (
    CALLS_PER_SYNC,
    CallBudgetExhaustedError,
    CallBudgetRepository,
    HoldingSnapshot,
    PortfolioClient,
    SnapshotRepository,
)
from app.shared.application.unit_of_work import UnitOfWork


class PortfolioSyncUnitOfWork(UnitOfWork, Protocol):
    @property
    def instruments(self) -> InstrumentRepository: ...

    @property
    def credentials(self) -> CredentialsRepository: ...

    @property
    def links(self) -> BrokerLinkRepository: ...

    @property
    def snapshots(self) -> SnapshotRepository: ...

    @property
    def budget(self) -> CallBudgetRepository: ...


@dataclass(frozen=True)
class SyncPortfolio:
    uow: PortfolioSyncUnitOfWork
    client: PortfolioClient
    cipher: CredentialCipher
    # Decisión del PO: corte al 80 % del cupo de 25.000 llamadas por mes, para no pagar extra.
    monthly_limit: int

    async def __call__(self, user_id: UUID, now: datetime) -> int | None:
        """Tenencias guardadas, o None si el usuario no tiene credenciales o cuenta vinculada."""
        async with self.uow:
            credentials = await self.uow.credentials.get_credentials(Broker.IOL)
            account_id = await self.uow.links.linked_account(Broker.IOL)
            if credentials is None or account_id is None:
                return None
            # Se descuenta antes de llamar: si IOL falla, las llamadas igual se gastaron.
            month = now.date().replace(day=1)
            allowed = await self.uow.budget.spend(
                Broker.IOL, month, CALLS_PER_SYNC, self.monthly_limit
            )
            await self.uow.commit()
        if not allowed:
            raise CallBudgetExhaustedError(
                f"Se llegó al tope de {self.monthly_limit} llamadas a IOL de este mes"
            )
        login = json.loads(self.cipher.decrypt(credentials.secret))
        # Sin una sesión abierta mientras espera a IOL.
        holdings = await self.client.portfolio(login["username"], login["password"])
        async with self.uow:
            catalog = {
                (i.ticker, i.market): i for i in await self.uow.instruments.list_instruments()
            }
            snapshots = []
            for h in holdings:
                instrument = catalog.get((h.ticker.strip().upper(), h.market))
                if instrument is None:
                    # Lo que no está en el catálogo se da de alta con los datos de IOL.
                    instrument = Instrument(user_id, h.ticker, h.name, h.type, h.market, h.currency)
                    await self.uow.instruments.add(instrument)
                    catalog[(instrument.ticker, instrument.market)] = instrument
                snapshots.append(
                    HoldingSnapshot(
                        user_id,
                        account_id,
                        instrument.id,
                        h.quantity,
                        h.average_price,
                        h.last_price,
                        now,
                    )
                )
            await self.uow.snapshots.replace(snapshots)
            await self.uow.commit()
        return len(snapshots)
