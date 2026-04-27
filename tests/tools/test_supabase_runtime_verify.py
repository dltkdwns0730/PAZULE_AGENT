from __future__ import annotations

import importlib.util
import json
import sys
from io import BytesIO
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "tools"
    / "supabase_runtime_verify.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "supabase_runtime_verify", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_selects_publishable_key_before_legacy_anon() -> None:
    module = load_module()

    selected = module.select_client_api_key(
        [
            {"name": "service_role", "api_key": "service-secret"},
            {"name": "anon", "api_key": "legacy-anon"},
            {"type": "publishable", "api_key": "sb_publishable_123"},
        ]
    )

    assert selected == "sb_publishable_123"


def test_fetches_project_client_key_without_logging_secret(monkeypatch, capsys) -> None:
    module = load_module()

    class FakeResponse:
        status = 200

        def read(self) -> bytes:
            return json.dumps(
                [{"type": "publishable", "api_key": "sb_publishable_abc"}]
            ).encode()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    monkeypatch.setattr(
        module.request, "urlopen", lambda _request, timeout: FakeResponse()
    )

    value = module.fetch_project_client_api_key("project-ref", "access-token")

    assert value == "sb_publishable_abc"
    assert "sb_publishable_abc" not in capsys.readouterr().out


def test_fetch_project_client_key_reports_forbidden_without_token(monkeypatch) -> None:
    module = load_module()

    forbidden = module.error.HTTPError(
        url="https://api.supabase.com/v1/projects/project-ref/api-keys",
        code=403,
        msg="Forbidden",
        hdrs=None,
        fp=BytesIO(b'{"message":"Forbidden"}'),
    )
    monkeypatch.setattr(
        module.request,
        "urlopen",
        lambda _request, timeout: (_ for _ in ()).throw(forbidden),
    )

    with pytest.raises(RuntimeError, match="Dashboard > Project Settings > API"):
        module.fetch_project_client_api_key("project-ref", "access-token")


@pytest.mark.parametrize("status", [200, 302])
def test_google_oauth_authorize_accepts_ready_status(monkeypatch, status) -> None:
    module = load_module()

    class FakeResponse:
        def __init__(self, status_code: int):
            self.status = status_code

        def read(self) -> bytes:
            return b""

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    monkeypatch.setattr(
        module.request,
        "urlopen",
        lambda _request, timeout: FakeResponse(status),
    )

    result = module.verify_google_oauth_authorize(
        "https://project.supabase.co",
        "sb_publishable_abc",
        "http://localhost:5173/auth/callback",
    )

    assert result.ready is True
    assert result.status == status


def test_google_oauth_authorize_reports_provider_or_key_errors(monkeypatch) -> None:
    module = load_module()

    error = module.error.HTTPError(
        url="https://project.supabase.co/auth/v1/authorize",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=BytesIO(b'{"msg":"Unsupported provider"}'),
    )
    monkeypatch.setattr(
        module.request,
        "urlopen",
        lambda _request, timeout: (_ for _ in ()).throw(error),
    )

    result = module.verify_google_oauth_authorize(
        "https://project.supabase.co",
        "sb_publishable_abc",
        "http://localhost:5173/auth/callback",
    )

    assert result.ready is False
    assert result.status == 400
    assert "Unsupported provider" in result.detail
