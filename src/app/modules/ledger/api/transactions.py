"""Endpoints de movimientos."""

import datetime as dt
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.modules.ledger.api.routes import LedgerUow
from app.modules.ledger.application.create_transaction import CreateTransaction
from app.modules.ledger.domain.category import CategoryKind
from app.shared.api.auth import CurrentUserId


class CreateTransactionRequest(BaseModel):
    account_id: UUID
    kind: CategoryKind
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    date: dt.date
    category_id: UUID
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = (
        None
    )


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    kind: CategoryKind
    # En JSON va como string decimal ("1500.50"), nunca como float.
    amount: Decimal
    date: dt.date
    category_id: UUID
    description: str | None


router = APIRouter(
    prefix="/transactions",
    tags=["movimientos"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"},
        status.HTTP_404_NOT_FOUND: {"description": "La cuenta o la categoría no existe"},
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un ingreso o un gasto",
    description="La categoría debe ser del mismo tipo y la cuenta no puede estar archivada.",
)
async def create_transaction(
    body: CreateTransactionRequest, user_id: CurrentUserId, uow: LedgerUow
) -> TransactionResponse:
    transaction = await CreateTransaction(uow=uow)(
        user_id,
        account_id=body.account_id,
        kind=body.kind,
        amount=body.amount,
        on=body.date,
        category_id=body.category_id,
        description=body.description,
    )
    return TransactionResponse.model_validate(transaction)
