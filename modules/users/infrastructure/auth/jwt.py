from __future__ import annotations

from datetime import UTC, datetime, timedelta

from modules.users.domain.exceptions import InvalidTokenError
from shared.config.settings import get_settings

# NOTE: this module is named jwt.py; the `import jwt` inside the functions below is an
# absolute import and resolves to the PyJWT package (requires: pip/uv package "pyjwt").
_ALGORITHM = "HS256"


def _secret() -> str:
    secret = get_settings().jwt_secret
    if not secret:
        raise RuntimeError("JWT_SECRET is not set. Add it to your .env file.")
    return secret


def create_access_token(user_id: str, role: str, expires_minutes: int | None = None) -> str:
    import jwt
    now = datetime.now(UTC)
    minutes = expires_minutes if expires_minutes is not None else get_settings().jwt_expire_minutes
    payload = {"sub": user_id, "role": role, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict:
    import jwt
    try:
        return jwt.decode(token, _secret(), algorithms=[_ALGORITHM])
    except jwt.PyJWTError as e:
        raise InvalidTokenError(str(e)) from e
