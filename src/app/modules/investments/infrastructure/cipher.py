"""Cifrado simétrico de las credenciales con Fernet (AES-128-CBC + HMAC-SHA256)."""

from cryptography.fernet import Fernet


class FernetCipher:
    def __init__(self, key: str) -> None:
        # La clave sale de CREDENTIALS_KEY: nunca se guarda en la base.
        self._fernet = Fernet(key)

    def encrypt(self, data: bytes) -> bytes:
        return self._fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        return self._fernet.decrypt(token)
