"""Endpoints del ledger."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.ledger.application.list_categories import ListCategories
from app.modules.ledger.application.manage_categories import (
    ArchiveCategory,
    CreateCategory,
    UpdateCategory,
)
from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.infrastructure.persistence import SqlAlchemyLedgerUnitOfWork
from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory

CategoryName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class CreateCategoryRequest(BaseModel):
    name: CategoryName
    kind: CategoryKind
    parent_id: UUID | None = None


class UpdateCategoryRequest(BaseModel):
    name: CategoryName | None = None
    # Mandar `"parent_id": null` la convierte en principal; no mandarlo deja el padre como está.
    parent_id: UUID | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    kind: CategoryKind
    parent_id: UUID | None
    archived_at: datetime | None


def get_ledger_uow(
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyLedgerUnitOfWork:
    return SqlAlchemyLedgerUnitOfWork(session_factory, user_id)


LedgerUow = Annotated[SqlAlchemyLedgerUnitOfWork, Depends(get_ledger_uow)]

router = APIRouter(
    prefix="/categories",
    tags=["categorías"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"},
        status.HTTP_404_NOT_FOUND: {"description": "La categoría no existe o es de otro usuario"},
    },
)


@router.get(
    "",
    summary="Listar mis categorías",
    description="La primera vez crea las categorías por defecto de ingresos y gastos.",
)
async def list_categories(
    user_id: CurrentUserId,
    uow: LedgerUow,
    include_archived: Annotated[bool, Query(description="Incluir las archivadas")] = False,
) -> list[CategoryResponse]:
    categories = await ListCategories(uow=uow)(user_id, include_archived=include_archived)
    return [CategoryResponse.model_validate(category) for category in categories]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear una categoría o subcategoría",
    responses={status.HTTP_409_CONFLICT: {"description": "Nombre repetido en ese lugar"}},
)
async def create_category(
    body: CreateCategoryRequest, user_id: CurrentUserId, uow: LedgerUow
) -> CategoryResponse:
    category = await CreateCategory(uow=uow)(
        user_id, name=body.name, kind=body.kind, parent_id=body.parent_id
    )
    return CategoryResponse.model_validate(category)


@router.patch(
    "/{category_id}",
    summary="Renombrar o mover una categoría",
    description="El tipo no cambia. Una categoría archivada no se puede editar (409).",
    responses={status.HTTP_409_CONFLICT: {"description": "Nombre repetido o archivada"}},
)
async def update_category(
    category_id: UUID, body: UpdateCategoryRequest, user_id: CurrentUserId, uow: LedgerUow
) -> CategoryResponse:
    category = await UpdateCategory(uow=uow)(
        user_id,
        category_id,
        name=body.name,
        change_parent="parent_id" in body.model_fields_set,
        parent_id=body.parent_id,
    )
    return CategoryResponse.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archivar una categoría",
    description="Archiva también sus subcategorías. Archivar dos veces no es error.",
)
async def archive_category(category_id: UUID, user_id: CurrentUserId, uow: LedgerUow) -> None:
    await ArchiveCategory(uow=uow)(user_id, category_id)
