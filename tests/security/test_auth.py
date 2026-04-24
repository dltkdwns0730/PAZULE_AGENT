import pytest

from app.security.auth import AuthError, extract_bearer_token


def test_extract_bearer_token_accepts_valid_header():
    assert extract_bearer_token("Bearer token-123") == "token-123"


@pytest.mark.parametrize("header", [None, "", "Basic abc", "Bearer"])
def test_extract_bearer_token_rejects_invalid_header(header):
    with pytest.raises(AuthError):
        extract_bearer_token(header)
