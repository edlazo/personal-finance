from uuid import uuid4

import pytest

from app.modules.identity.application.profile import GetProfile, UpdatePreferences
from app.modules.identity.domain.user import User
from app.shared.domain.auth import InvalidTokenError
from app.shared.domain.rates import RateType
from fakes.identity import FakeUnitOfWork


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def user(uow: FakeUnitOfWork) -> User:
    user = User(email="ana@example.com", name="Ana", password_hash="hash")
    uow.users.by_email[user.email] = user
    return user


async def test_profile_starts_with_mep(uow: FakeUnitOfWork, user: User) -> None:
    profile = await GetProfile(uow=uow)(user.id)

    assert profile.email == "ana@example.com"
    assert profile.default_rate_type is RateType.MEP


async def test_update_preferences_saves_the_new_rate(uow: FakeUnitOfWork, user: User) -> None:
    updated = await UpdatePreferences(uow=uow)(user.id, default_rate_type=RateType.BLUE)

    assert updated.default_rate_type is RateType.BLUE
    assert uow.users.by_email[user.email].default_rate_type is RateType.BLUE
    assert uow.committed


async def test_a_deleted_user_needs_to_log_in_again(uow: FakeUnitOfWork) -> None:
    with pytest.raises(InvalidTokenError):
        await GetProfile(uow=uow)(uuid4())
    with pytest.raises(InvalidTokenError):
        await UpdatePreferences(uow=uow)(uuid4(), default_rate_type=RateType.CCL)
