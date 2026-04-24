"""Supabase JWT verification helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings


class AuthError(PermissionError):
    """Raised when a bearer token is missing or invalid."""


@dataclass(frozen=True)
class AuthPrincipal:
    user_id: str
    email: str | None
    claims: dict[str, Any]


def extract_bearer_token(authorization_header: str | None) -> str:
    """Extract a bearer token from an Authorization header."""
    if not authorization_header:
        raise AuthError("authorization_required")

    scheme, _, token = authorization_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError("invalid_authorization_header")
    return token


def _require_pyjwt():
    try:
        import jwt
        from jwt import PyJWKClient
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "PyJWT is not installed. Run `uv sync --dev` after platform "
            "dependencies are added."
        ) from exc
    return jwt, PyJWKClient


def verify_supabase_token(token: str) -> AuthPrincipal:
    """Verify a Supabase access token and return the authenticated principal."""
    if not settings.SUPABASE_JWKS_URL:
        raise AuthError("supabase_jwks_url_not_configured")

    jwt, PyJWKClient = _require_pyjwt()
    jwks_client = PyJWKClient(settings.SUPABASE_JWKS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256", "ES256"],
        audience=settings.SUPABASE_JWT_AUDIENCE,
        options={"require": ["sub", "exp"]},
    )

    return AuthPrincipal(
        user_id=claims["sub"],
        email=claims.get("email"),
        claims=claims,
    )
