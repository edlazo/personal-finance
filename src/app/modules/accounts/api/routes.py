"""Endpoints de cuentas."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.accounts.application.create_account import CreateAccount
from app.modules.accounts.application.manage_accounts import (
    ArchiveAccount,
    ListAccounts,
    UpdateAccount,
)
from app.modules.accounts.domain.account import AccountType
from app.modules.accounts.infrastructure.persistence import SqlAlchemyAccountsUnitOfWork
from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory
from app.shared.domain.money import Currency


class CreateAccountRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    type: AccountType
    currency: Currency
    initial_balance: Decimal = Field(default=Decimal("0"), max_digits=20, decimal_places=2)


class UpdateAccountRequest(BaseModel):
    name: Annotated[
        str | None, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ] = None
    currency: Currency | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: AccountType
    currency: Currency
    # En JSON va como string decimal ("1500.50"), nunca como float.
    initial_balance: Decimal
    created_at: datetime
    archived_at: datetime | None


def get_accounts_uow(
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyAccountsUnitOfWork:
    return SqlAlchemyAccountsUnitOfWork(session_factory, user_id)


AccountsUow = Annotated[SqlAlchemyAccountsUnitOfWork, Depends(get_accounts_uow)]

router = APIRouter(
    prefix="/accounts",
    tags=["cuentas"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"},
        status.HTTP_404_NOT_FOUND: {"description": "La cuenta no existe o es de otro usuario"},
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear una cuenta",
    description="Saldo inicial con hasta 2 decimales; solo las comitentes admiten negativo.",
    responses={
        status.HTTP_409_CONFLICT: {"description": "Ya hay una cuenta activa con ese nombre"},
    },
)
async def create_account(
    body: CreateAccountRequest, user_id: CurrentUserId, uow: AccountsUow
) -> AccountResponse:
    account = await CreateAccount(uow=uow)(
        user_id=user_id,
        name=body.name,
        account_type=body.type,
        currency=body.currency,
        initial_balance=body.initial_balance,
    )
    return AccountResponse.model_validate(account)


@router.get("", summary="Listar mis cuentas")
async def list_accounts(
    uow: AccountsUow,
    include_archived: Annotated[bool, Query(description="Incluir las archivadas")] = False,
) -> list[AccountResponse]:
    accounts = await ListAccounts(uow=uow)(include_archived=include_archived)
    return [AccountResponse.model_validate(account) for account in accounts]


@router.patch(
    "/{account_id}",
    summary="Editar una cuenta",
    description="Cambia nombre y/o moneda. Una cuenta archivada no se puede editar (409).",
    responses={status.HTTP_409_CONFLICT: {"description": "Nombre repetido o cuenta archivada"}},
)
async def update_account(
    account_id: UUID, body: UpdateAccountRequest, uow: AccountsUow
) -> AccountResponse:
    account = await UpdateAccount(uow=uow)(account_id, name=body.name, currency=body.currency)
    return AccountResponse.model_validate(account)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archivar una cuenta",
    description="No la borra: deja de aparecer en el listado. Archivar dos veces no es error.",
)
async def archive_account(account_id: UUID, uow: AccountsUow) -> None:
    await ArchiveAccount(uow=uow)(account_id)
