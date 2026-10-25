"""Endpoints de movimientos."""

import datetime as dt
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.modules.ledger.api.routes import LedgerUow
from app.modules.ledger.application.create_transaction import CreateTransaction
from app.modules.ledger.application.list_transactions import ListTransactions
from app.modules.ledger.application.manage_transactions import (
    DeleteTransaction,
    UpdateTransaction,
)
from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.transaction import TransactionFilter
from app.shared.api.auth import CurrentUserId

Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None
Amount = Annotated[Decimal, Field(gt=0, max_digits=20, decimal_places=2)]


class CreateTransactionRequest(BaseModel):
    account_id: UUID
    kind: CategoryKind
    amount: Amount
    date: dt.date
    category_id: UUID
    description: Description = None


class UpdateTransactionRequest(BaseModel):
    """Lo que no se manda no cambia; `"description": ""` la borra."""

    account_id: UUID | None = None
    kind: CategoryKind | None = None
    amount: Amount | None = None
    date: dt.date | None = None
    category_id: UUID | None = None
    description: Description = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    kind: CategoryKind
    # En JSON va como string decimal ("1500.50"), nunca como float.
    amount: Decimal
    date: dt.date
    category_id: UUID | None
    description: str | None
    # Solo en las dos patas de una transferencia (POST /transfers).
    transfer_group_id: UUID | None


class TransactionQuery(BaseModel):
    date_from: dt.date | None = Field(None, description="Desde esta fecha (inclusive)")
    date_to: dt.date | None = Field(None, description="Hasta esta fecha (inclusive)")
    account_id: UUID | None = None
    category_id: UUID | None = Field(None, description="Incluye sus subcategorías")
    kind: CategoryKind | None = None
    q: str | None = Field(None, max_length=200, description="Texto en la descripción")
    amount_min: Decimal | None = Field(None, ge=0, decimal_places=2)
    amount_max: Decimal | None = Field(None, ge=0, decimal_places=2)
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class TransactionPageResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int


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


@router.get(
    "",
    summary="Listar mis movimientos",
    description="Ordenados por fecha, del más reciente al más viejo, con el total para paginar.",
)
async def list_transactions(
    params: Annotated[TransactionQuery, Query()], uow: LedgerUow
) -> TransactionPageResponse:
    filters = TransactionFilter(
        date_from=params.date_from,
        date_to=params.date_to,
        account_id=params.account_id,
        kind=params.kind,
        text=params.q,
        amount_min=params.amount_min,
        amount_max=params.amount_max,
    )
    page = await ListTransactions(uow=uow)(
        filters, category_id=params.category_id, limit=params.limit, offset=params.offset
    )
    return TransactionPageResponse(
        items=[TransactionResponse.model_validate(t) for t in page.items],
        total=page.total,
        limit=params.limit,
        offset=params.offset,
    )


@router.patch(
    "/{transaction_id}",
    summary="Editar un movimiento",
    description=(
        "En una transferencia solo se editan monto, fecha y descripción, y cambian las dos patas."
    ),
    responses={status.HTTP_409_CONFLICT: {"description": "La cuenta está archivada"}},
)
async def update_transaction(
    transaction_id: UUID, body: UpdateTransactionRequest, uow: LedgerUow
) -> TransactionResponse:
    transaction = await UpdateTransaction(uow=uow)(
        transaction_id,
        account_id=body.account_id,
        kind=body.kind,
        category_id=body.category_id,
        amount=body.amount,
        on=body.date,
        description=body.description,
    )
    return TransactionResponse.model_validate(transaction)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un movimiento",
    description="Lo borra definitivamente; si es una transferencia, borra las dos patas.",
    responses={status.HTTP_409_CONFLICT: {"description": "La cuenta está archivada"}},
)
async def delete_transaction(transaction_id: UUID, uow: LedgerUow) -> None:
    await DeleteTransaction(uow=uow)(transaction_id)
