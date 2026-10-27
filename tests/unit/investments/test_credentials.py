import json
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet, InvalidToken
from pydantic import SecretStr, ValidationError

from app.config import Settings
from app.modules.investments.application.manage_credentials import (
    CredentialsStatus,
    DeleteCredentials,
    SaveCredentials,
)
from app.modules.investments.domain.credentials import Broker, InvalidCredentialsError
from app.modules.investments.infrastructure.cipher import FernetCipher
from fakes.investments import FakeCredentialsUnitOfWork

USER = uuid4()
PASSWORD = "clave-de-iol"


async def test_only_the_cipher_text_and_a_hint_are_stored() -> None:
    uow, cipher = FakeCredentialsUnitOfWork(), FernetCipher(Fernet.generate_key().decode())
    save = SaveCredentials(uow, cipher)

    await save(USER, Broker.IOL, " elias@example.com ", PASSWORD)
    await save(USER, Broker.IOL, "otro", "otra-clave")

    stored = await CredentialsStatus(uow)(Broker.IOL)
    assert stored is not None
    assert (stored.username_hint, len(uow.credentials.items)) == ("ot***", 1)
    assert PASSWORD.encode() not in stored.secret
    assert json.loads(cipher.decrypt(stored.secret)) == {
        "username": "otro",
        "password": "otra-clave",
    }
    assert PASSWORD not in repr(stored)


async def test_delete_is_idempotent_and_blank_values_are_rejected() -> None:
    uow = FakeCredentialsUnitOfWork()
    save = SaveCredentials(uow, FernetCipher(Fernet.generate_key().decode()))

    with pytest.raises(InvalidCredentialsError):
        await save(USER, Broker.IOL, "  ", PASSWORD)
    await save(USER, Broker.IOL, "elias", PASSWORD)
    await DeleteCredentials(uow)(Broker.IOL)
    await DeleteCredentials(uow)(Broker.IOL)

    assert await CredentialsStatus(uow)(Broker.IOL) is None


def test_another_key_cannot_read_them_and_production_needs_its_own_key() -> None:
    token = FernetCipher(Fernet.generate_key().decode()).encrypt(b"secreto")
    with pytest.raises(InvalidToken):
        FernetCipher(Fernet.generate_key().decode()).decrypt(token)
    real = SecretStr("x" * 40)
    with pytest.raises(ValidationError, match="CREDENTIALS_KEY"):
        Settings(_env_file=None, environment="production", jwt_secret=real)
    key = SecretStr(Fernet.generate_key().decode())
    settings = Settings(
        _env_file=None, environment="production", jwt_secret=real, credentials_key=key
    )
    assert settings.credentials_key == key
