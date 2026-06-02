import pytest

from app.security.auth import AuthError, extract_bearer_token, verify_supabase_token


def test_extract_bearer_token_accepts_valid_header():
    assert extract_bearer_token("Bearer token-123") == "token-123"


@pytest.mark.parametrize("header", [None, "", "Basic abc", "Bearer"])
def test_extract_bearer_token_rejects_invalid_header(header):
    with pytest.raises(AuthError):
        extract_bearer_token(header)


def test_verify_supabase_token_wraps_jwks_errors_as_auth_error(monkeypatch):
    class FakeJwt:
        @staticmethod
        def decode(*_args, **_kwargs):
            raise AssertionError("decode should not run when signing key fails")

    class FakeJwksClient:
        def __init__(self, _url):
            pass

        def get_signing_key_from_jwt(self, _token):
            raise RuntimeError("invalid token")

    monkeypatch.setattr("app.security.auth.settings.DEMO_AUTH_ENABLED", False)
    monkeypatch.setattr(
        "app.security.auth.settings.SUPABASE_JWKS_URL",
        "https://project.supabase.co/auth/v1/.well-known/jwks.json",
    )
    monkeypatch.setattr(
        "app.security.auth._require_pyjwt",
        lambda: (FakeJwt, FakeJwksClient),
    )

    with pytest.raises(AuthError, match="invalid_or_expired_token"):
        verify_supabase_token("bad.jwt.token")
