"""Endpoint de transferencias entre cuentas propias."""

import datetime as dt
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


class TransferResponse(BaseModel):
    transfer_group_id: UUID
    outgoing: TransactionResponse
    incoming: TransactionResponse


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
    description="Cuentas distintas, de la misma moneda y no archivadas. No es ingreso ni gasto.",
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
    )
    return TransferResponse(
        transfer_group_id=result.group_id,
        outgoing=TransactionResponse.model_validate(result.outgoing),
        incoming=TransactionResponse.model_validate(result.incoming),
    )
