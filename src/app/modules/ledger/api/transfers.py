"""Endpoint de transferencias entre cuentas propias."""

import datetime as dt
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.modules.ledger.api.routes import LedgerUow
from app.modules.ledger.api.transactions import Amount, Description, TransactionResponse
from app.modules.ledger.application.create_transfer import CreateTransfer
from app.shared.api.auth import CurrentUserId


class CreateTransferRequest(BaseModel):
    from_account_id: UUID
    to_account_id: UUID
    amount: Amount
    date: dt.date
    description: Description = None
    # Compra o venta de dólares: lo que entra a la cuenta destino, en su moneda.
    to_amount: Amount | None = None
    # Opcional: gasto aparte en la cuenta origen, en la categoría "Comisiones".
    fee: Amount | None = None


class TransferResponse(BaseModel):
    transfer_group_id: UUID
    outgoing: TransactionResponse
    incoming: TransactionResponse
    # Pesos por dólar de la operación; solo entre monedas distintas.
    exchange_rate: Decimal | None
    fee: TransactionResponse | None


router = APIRouter(
    prefix="/transfers",
    tags=["movimientos"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"},
        status.HTTP_404_NOT_FOUND: {"description": "Alguna de las cuentas no existe"},
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Transferir entre mis cuentas",
    description=(
        "Cuentas distintas, propias y no archivadas; no es ingreso ni gasto. Entre ARS y USD "
        "(compra o venta de dólares) hace falta `to_amount` y se devuelve el tipo de cambio."
    ),
)
async def create_transfer(
    body: CreateTransferRequest, user_id: CurrentUserId, uow: LedgerUow
) -> TransferResponse:
    result = await CreateTransfer(uow=uow)(
        user_id,
        source_id=body.from_account_id,
        target_id=body.to_account_id,
        amount=body.amount,
        on=body.date,
        description=body.description,
        received=body.to_amount,
        fee=body.fee,
    )
    return TransferResponse(
        transfer_group_id=result.group_id,
        outgoing=TransactionResponse.model_validate(result.outgoing),
        incoming=TransactionResponse.model_validate(result.incoming),
        exchange_rate=result.exchange_rate,
        fee=None if result.fee is None else TransactionResponse.model_validate(result.fee),
    )
