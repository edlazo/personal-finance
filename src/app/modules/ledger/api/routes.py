"""Endpoints del ledger."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.ledger.application.list_categories import ListCategories
from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.infrastructure.persistence import SqlAlchemyLedgerUnitOfWork
from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    kind: CategoryKind


def get_ledger_uow(
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyLedgerUnitOfWork:
    return SqlAlchemyLedgerUnitOfWork(session_factory, user_id)


LedgerUow = Annotated[SqlAlchemyLedgerUnitOfWork, Depends(get_ledger_uow)]

router = APIRouter(
    prefix="/categories",
    tags=["categorías"],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"}},
)


@router.get(
    "",
    summary="Listar mis categorías",
    description="La primera vez crea las categorías por defecto de ingresos y gastos.",
)
async def list_categories(user_id: CurrentUserId, uow: LedgerUow) -> list[CategoryResponse]:
    categories = await ListCategories(uow=uow)(user_id)
    return [CategoryResponse.model_validate(category) for category in categories]
