"""Endpoints de reglas de movimientos recurrentes (US-043)."""

import datetime as dt
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from app.modules.ledger.api.routes import LedgerUow
from app.modules.ledger.api.transactions import Amount, Description, TransactionResponse
from app.modules.ledger.application.generate_recurring import (
    ConfirmPending,
    DiscardPending,
    ListPending,
)
from app.modules.ledger.application.manage_recurring import (
    CreateRecurring,
    DeleteRecurring,
    GetRecurring,
    ListRecurring,
    UpdateRecurring,
)
from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.recurring import Frequency, RecurringRule
from app.shared.api.auth import CurrentUserId


class CreateRecurringRequest(BaseModel):
    account_id: UUID
    kind: CategoryKind
    amount: Amount
    category_id: UUID
    # Semanal, mensual o anual: el día sale de la fecha de inicio.
    frequency: Frequency
    start_date: dt.date
    end_date: dt.date | None = None
    description: Description = None
    # true: cada ocurrencia queda pendiente, fuera del saldo, hasta confirmarla.
    needs_confirmation: bool = False


class UpdateRecurringRequest(BaseModel):
    """Lo que no se manda no cambia; `"end_date": null` quita la fecha de fin."""

    account_id: UUID | None = None
    kind: CategoryKind | None = None
    amount: Amount | None = None
    category_id: UUID | None = None
    frequency: Frequency | None = None
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    description: Description = None
    # true pausa la regla; false la reanuda.
    paused: bool | None = None
    needs_confirmation: bool | None = None


class RecurringResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    kind: CategoryKind
    amount: Decimal
    category_id: UUID
    frequency: Frequency
    start_date: dt.date
    end_date: dt.date | None
    description: str | None
    paused: bool
    needs_confirmation: bool


class PendingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: UUID
    date: dt.date
    amount: Decimal


class ConfirmPendingRequest(BaseModel):
    # Sin monto, se usa el de la ocurrencia.
    amount: Amount | None = None


# Los únicos campos que se pueden vaciar con null.
NULLABLE = {"end_date", "description"}

router = APIRouter(
    prefix="/recurring",
    tags=["recurrentes"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"},
        status.HTTP_404_NOT_FOUND: {
            "description": "La regla, la cuenta o la categoría no existe o es de otro usuario"
        },
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear una regla de ingreso o gasto recurrente",
    description="Se valida como un movimiento: cuenta activa y categoría del mismo tipo.",
)
async def create_recurring(
    body: CreateRecurringRequest, user_id: CurrentUserId, uow: LedgerUow
) -> RecurringResponse:
    rule = RecurringRule(user_id, **body.model_dump())
    return RecurringResponse.model_validate(await CreateRecurring(uow=uow)(rule))


@router.get("", summary="Mis reglas recurrentes", description="Por fecha de inicio.")
async def list_recurring(uow: LedgerUow) -> list[RecurringResponse]:
    return [RecurringResponse.model_validate(r) for r in await ListRecurring(uow=uow)()]


# Antes que /{rule_id}: si no, "pending" se toma como un id.
@router.get(
    "/pending",
    summary="Ocurrencias pendientes de confirmar",
    description="No cuentan en saldos ni reportes hasta confirmarlas. Por fecha.",
)
async def list_pending(uow: LedgerUow) -> list[PendingResponse]:
    return [PendingResponse.model_validate(p) for p in await ListPending(uow=uow)()]


@router.post(
    "/pending/{pending_id}/confirm",
    status_code=status.HTTP_201_CREATED,
    summary="Confirmar una ocurrencia pendiente",
    description="Crea el movimiento con los datos actuales de la regla; el monto se puede ajustar.",
)
async def confirm_pending(
    pending_id: UUID, body: ConfirmPendingRequest, uow: LedgerUow
) -> TransactionResponse:
    movement = await ConfirmPending(uow=uow)(pending_id, body.amount)
    return TransactionResponse.model_validate(movement)


@router.delete(
    "/pending/{pending_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Descartar una ocurrencia pendiente",
)
async def discard_pending(pending_id: UUID, uow: LedgerUow) -> None:
    await DiscardPending(uow=uow)(pending_id)


@router.get("/{rule_id}", summary="Ver una regla recurrente")
async def get_recurring(rule_id: UUID, uow: LedgerUow) -> RecurringResponse:
    return RecurringResponse.model_validate(await GetRecurring(uow=uow)(rule_id))


@router.patch(
    "/{rule_id}",
    summary="Editar, pausar o reanudar una regla recurrente",
    description="Solo cambian los campos enviados. `paused` pausa (true) o reanuda (false).",
)
async def update_recurring(
    rule_id: UUID, body: UpdateRecurringRequest, uow: LedgerUow
) -> RecurringResponse:
    changes = body.model_dump(exclude_unset=True)
    changes = {k: v for k, v in changes.items() if v is not None or k in NULLABLE}
    return RecurringResponse.model_validate(await UpdateRecurring(uow=uow)(rule_id, changes))


@router.delete(
    "/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Borrar una regla recurrente"
)
async def delete_recurring(rule_id: UUID, uow: LedgerUow) -> None:
    await DeleteRecurring(uow=uow)(rule_id)
