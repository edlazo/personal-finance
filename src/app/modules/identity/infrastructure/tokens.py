"""Tokens JWT (HS256): access de corta vida y refresh."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

import jwt

from app.modules.identity.domain.user import InvalidTokenError, TokenPair

ALGORITHM = "HS256"


class JwtTokenService:
    def __init__(
        self,
        secret: str,
        access_ttl: timedelta,
        refresh_ttl: timedelta,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._secret = secret
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl
        self._clock = clock

    def issue(self, user_id: UUID) -> TokenPair:
        now = self._clock()
        return TokenPair(
            access_token=self._encode(user_id, "access", now, self._access_ttl),
            refresh_token=self._encode(user_id, "refresh", now, self._refresh_ttl),
            expires_in=int(self._access_ttl.total_seconds()),
        )

    def decode_access(self, token: str) -> UUID:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                options={"require": ["exp", "iat", "sub"]},
            )
            # Un refresh token no sirve para llamar a la API.
            if claims.get("type") != "access":
                raise InvalidTokenError
            return UUID(claims["sub"])
        except (jwt.PyJWTError, ValueError) as exc:
            raise InvalidTokenError from exc

    def _encode(
        self, user_id: UUID, kind: Literal["access", "refresh"], now: datetime, ttl: timedelta
    ) -> str:
        claims = {"sub": str(user_id), "type": kind, "iat": now, "exp": now + ttl}
        # jti: identifica cada token (la rotación del refresh llega en PF-25).
        return jwt.encode({**claims, "jti": uuid4().hex}, self._secret, algorithm=ALGORITHM)
