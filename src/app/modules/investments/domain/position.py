"""Tenencia y resultados por cuenta e instrumento, con costo promedio ponderado."""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

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
    # MANUAL o LAST_TRADE: el de fecha más reciente (decisión del PO).
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


def build_positions(
    trades: list[Trade],
    instruments: dict[UUID, Instrument],
    prices: dict[UUID, InstrumentPrice] | None = None,
) -> list[Position]:
    """Recorre las operaciones en orden: la compra suma al costo lo que salió de la cuenta y la
    venta realiza lo que entró menos el costo promedio de lo vendido."""
    prices = prices or {}
    state: dict[tuple[UUID, UUID], tuple[Decimal, Decimal, Decimal, Trade]] = {}
    for trade in sorted(trades, key=lambda t: (t.date, t.created_at)):
        key = (trade.account_id, trade.instrument_id)
        zero = Decimal("0")
        quantity, cost, realized, _ = state.get(key, (zero, zero, zero, trade))
        cash = trade.cash(instruments[trade.instrument_id].quote_unit)
        if trade.side is TradeSide.BUY:
            quantity, cost = quantity + trade.quantity, cost + cash
        else:
            sold_cost = (cost * trade.quantity / quantity).quantize(CENTS, ROUND_HALF_UP)
            quantity, cost, realized = (
                quantity - trade.quantity,
                cost - sold_cost,
                realized + cash - sold_cost,
            )
        state[key] = (quantity, cost, realized, trade)
    positions = []
    for (account_id, instrument_id), (quantity, cost, realized, last) in state.items():
        manual = prices.get(instrument_id)
        # A igual fecha gana el precio cargado a mano.
        if manual is not None and manual.date >= last.date:
            price, source, on = manual.price, "MANUAL", manual.date
        else:
            price, source, on = last.price, "LAST_TRADE", last.date
        instrument = instruments[instrument_id]
        positions.append(
            Position(account_id, instrument, quantity, cost, realized, price, source, on)
        )
    return sorted(positions, key=lambda p: (p.instrument.ticker, str(p.account_id)))
