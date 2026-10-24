from uuid import uuid4

import pytest

from app.modules.identity.application.sessions import Logout, RefreshSession
from app.shared.domain.auth import InvalidTokenError, TokenPair
from fakes.identity import FakeTokens, FakeUnitOfWork


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
async def session(uow: FakeUnitOfWork) -> TokenPair:
    """Una sesión abierta, como la deja el login."""
    tokens = FakeTokens().issue(uuid4())
    await uow.refresh_tokens.add(tokens.refresh)
    return tokens


async def test_refresh_rotates_the_token(uow: FakeUnitOfWork, session: TokenPair) -> None:
    new = await RefreshSession(uow=uow, tokens=FakeTokens())(session.refresh_token)

    assert new.refresh.user_id == session.refresh.user_id
    assert session.refresh.jti in uow.refresh_tokens.revoked
    assert new.refresh.jti in uow.refresh_tokens.active


async def test_reusing_a_rotated_token_is_rejected(uow: FakeUnitOfWork, session: TokenPair) -> None:
    refresh = RefreshSession(uow=uow, tokens=FakeTokens())
    await refresh(session.refresh_token)

    with pytest.raises(InvalidTokenError):
        await refresh(session.refresh_token)


async def test_logout_revokes_and_is_idempotent(uow: FakeUnitOfWork, session: TokenPair) -> None:
    logout = Logout(uow=uow, tokens=FakeTokens())
    await logout(session.refresh_token)
    await logout(session.refresh_token)

    with pytest.raises(InvalidTokenError):
        await RefreshSession(uow=uow, tokens=FakeTokens())(session.refresh_token)
