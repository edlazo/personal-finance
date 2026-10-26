"""Tenencia y resultados por cuenta e instrumento, con costo promedio ponderado."""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.modules.investments.domain.event import EventKind, InstrumentEvent
from app.modules.investments.domain.instrument import Instrument
from app.modules.investments.domain.price import InstrumentPrice
from app.modules.investments.domain.trade import CENTS, PRICE_PRECISION, Trade, TradeSide


@dataclass(frozen=True)
class Position:
    account_id: UUID
    instrument: Instrument
    quantity: Decimal
    # Lo que costó la tenencia actual, con las comisiones de compra (decisión del PO).
    cost: Decimal
    realized_pnl: Decimal
    current_price: Decimal
    # MANUAL, API o LAST_TRADE: el de fecha más reciente (decisión del PO).
    price_source: str
    price_date: date

    @property
    def average_price(self) -> Decimal:
        """En la misma unidad que el precio (cada 100 VN en bonos y ONs)."""
        if not self.quantity:
            return Decimal("0")
        unit_cost = self.cost / self.quantity * self.instrument.quote_unit
        return unit_cost.quantize(PRICE_PRECISION, ROUND_HALF_UP)

    @property
    def valuation(self) -> Decimal:
        value = self.current_price * self.quantity / self.instrument.quote_unit
        return value.quantize(CENTS, ROUND_HALF_UP)

    @property
    def unrealized_pnl(self) -> Decimal:
        return self.valuation - self.cost

    @property
    def unrealized_pnl_pct(self) -> Decimal:
        if not self.cost:
            return Decimal("0")
        return (self.unrealized_pnl / self.cost * 100).quantize(CENTS, ROUND_HALF_UP)


def _release(
    quantity: Decimal, cost: Decimal, realized: Decimal, out: Decimal, cash: Decimal
) -> tuple[Decimal, Decimal, Decimal]:
    """Sale `out` de la tenencia (venta o amortización) cobrando `cash`."""
    out_cost = (cost * out / quantity).quantize(CENTS, ROUND_HALF_UP)
    return quantity - out, cost - out_cost, realized + cash - out_cost


def build_positions(
    trades: list[Trade],
    instruments: dict[UUID, Instrument],
    prices: dict[UUID, InstrumentPrice] | None = None,
    events: list[InstrumentEvent] | None = None,
) -> list[Position]:
    """Recorre operaciones y eventos en orden: la compra suma al costo lo que salió de la cuenta,
    la venta y la amortización realizan lo cobrado menos el costo promedio de lo que sale, y los
    dividendos y cupones suman al resultado realizado (decisiones del PO)."""
    prices = prices or {}
    state: dict[tuple[UUID, UUID], tuple[Decimal, Decimal, Decimal, Trade]] = {}
    timeline: list[Trade | InstrumentEvent] = [*trades, *(events or [])]
    for item in sorted(timeline, key=lambda i: (i.date, i.created_at)):
        key = (item.account_id, item.instrument_id)
        zero = Decimal("0")
        if isinstance(item, InstrumentEvent):
            # Siempre hay una compra antes: un evento pide tenencia en la cuenta.
            quantity, cost, realized, last = state[key]
            if item.kind is EventKind.AMORTIZATION and item.nominal is not None:
                quantity, cost, realized = _release(
                    quantity, cost, realized, item.nominal, item.amount
                )
            else:
                realized += item.amount
            state[key] = (quantity, cost, realized, last)
            continue
        trade = item
        quantity, cost, realized, _ = state.get(key, (zero, zero, zero, trade))
        cash = trade.cash(instruments[trade.instrument_id].quote_unit)
        if trade.side is TradeSide.BUY:
            quantity, cost = quantity + trade.quantity, cost + cash
        else:
            quantity, cost, realized = _release(quantity, cost, realized, trade.quantity, cash)
        state[key] = (quantity, cost, realized, trade)
    positions = []
    for (account_id, instrument_id), (quantity, cost, realized, last) in state.items():
        stored = prices.get(instrument_id)
        # A igual fecha gana el precio guardado (manual o de la API) sobre la operación.
        if stored is not None and stored.date >= last.date:
            price, source, on = stored.price, stored.source.value, stored.date
        else:
            price, source, on = last.price, "LAST_TRADE", last.date
        instrument = instruments[instrument_id]
        positions.append(
            Position(account_id, instrument, quantity, cost, realized, price, source, on)
        )
    return sorted(positions, key=lambda p: (p.instrument.ticker, str(p.account_id)))
