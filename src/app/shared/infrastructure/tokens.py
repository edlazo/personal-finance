"""Tokens JWT (HS256): access de corta vida y refresh."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

import jwt

from app.shared.domain.auth import InvalidTokenError, RefreshClaims, TokenPair

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
        refresh = RefreshClaims(user_id, uuid4().hex, now + self._refresh_ttl)
        return TokenPair(
            access_token=self._encode(user_id, "access", now, now + self._access_ttl, uuid4().hex),
            refresh_token=self._encode(user_id, "refresh", now, refresh.expires_at, refresh.jti),
            expires_in=int(self._access_ttl.total_seconds()),
            refresh=refresh,
        )

    def decode_access(self, token: str) -> UUID:
        return UUID(self._decode(token, "access")["sub"])

    def decode_refresh(self, token: str) -> RefreshClaims:
        claims = self._decode(token, "refresh")
        return RefreshClaims(
            UUID(claims["sub"]), claims["jti"], datetime.fromtimestamp(claims["exp"], UTC)
        )

    def _decode(self, token: str, kind: Literal["access", "refresh"]) -> dict[str, Any]:
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                options={"require": ["exp", "iat", "sub", "jti"]},
            )
            # Un refresh no sirve para llamar a la API, ni un access para renovar la sesión.
            if claims.get("type") != kind:
                raise InvalidTokenError
            UUID(claims["sub"])
        except (jwt.PyJWTError, ValueError) as exc:
            raise InvalidTokenError from exc
        return claims

    def _encode(
        self,
        user_id: UUID,
        kind: Literal["access", "refresh"],
        now: datetime,
        expires_at: datetime,
        jti: str,
    ) -> str:
        claims = {"sub": str(user_id), "type": kind, "iat": now, "exp": expires_at, "jti": jti}
        return jwt.encode(claims, self._secret, algorithm=ALGORITHM)
