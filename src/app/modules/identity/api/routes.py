"""Endpoints de autenticación."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.identity.application.login_user import LoginUser
from app.modules.identity.application.register_user import RegisterUser
from app.modules.identity.application.sessions import Logout, RefreshSession
from app.modules.identity.domain.user import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from app.modules.identity.infrastructure.persistence import (
    Argon2PasswordHasher,
    SqlAlchemyIdentityUnitOfWork,
)
from app.shared.api.auth import get_token_service
from app.shared.api.dependencies import get_session_factory
from app.shared.domain.auth import TokenPair
from app.shared.domain.rates import RateType
from app.shared.infrastructure.tokens import JwtTokenService


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class LoginRequest(BaseModel):
    email: EmailStr
    # Sin largo mínimo: no se revelan reglas al que prueba credenciales; sí un tope de costo.
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 - tipo estándar de OAuth2, no un secreto
    expires_in: int


def token_response(tokens: TokenPair) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    default_rate_type: RateType
    created_at: datetime


def get_register_user(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> RegisterUser:
    return RegisterUser(
        uow=SqlAlchemyIdentityUnitOfWork(session_factory), hasher=Argon2PasswordHasher()
    )


def get_login_user(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
    tokens: Annotated[JwtTokenService, Depends(get_token_service)],
) -> LoginUser:
    return LoginUser(
        uow=SqlAlchemyIdentityUnitOfWork(session_factory),
        hasher=Argon2PasswordHasher(),
        tokens=tokens,
    )


def get_identity_uow(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyIdentityUnitOfWork:
    return SqlAlchemyIdentityUnitOfWork(session_factory)


IdentityUow = Annotated[SqlAlchemyIdentityUnitOfWork, Depends(get_identity_uow)]
Tokens = Annotated[JwtTokenService, Depends(get_token_service)]


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario",
    description="Crea el usuario con la cotización MEP como preferencia. Nunca devuelve el hash.",
    responses={status.HTTP_409_CONFLICT: {"description": "El email ya está registrado"}},
)
async def register(
    body: RegisterRequest, register_user: Annotated[RegisterUser, Depends(get_register_user)]
) -> UserResponse:
    user = await register_user(email=body.email, password=body.password, name=body.name)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    summary="Iniciar sesión",
    description="Devuelve un access token (15 min) y un refresh token (7 días).",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Email o contraseña incorrectos"}},
)
async def login(
    body: LoginRequest, login_user: Annotated[LoginUser, Depends(get_login_user)]
) -> TokenResponse:
    return token_response(await login_user(email=body.email, password=body.password))


@router.post(
    "/refresh",
    summary="Renovar la sesión",
    description="Emite tokens nuevos y revoca el refresh token usado (rotación).",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Refresh token inválido o usado"}},
)
async def refresh(body: RefreshRequest, uow: IdentityUow, tokens: Tokens) -> TokenResponse:
    return token_response(await RefreshSession(uow=uow, tokens=tokens)(body.refresh_token))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar la sesión",
    description="Revoca el refresh token. Cerrar una sesión ya cerrada no es un error.",
)
async def logout(body: RefreshRequest, uow: IdentityUow, tokens: Tokens) -> None:
    await Logout(uow=uow, tokens=tokens)(body.refresh_token)
