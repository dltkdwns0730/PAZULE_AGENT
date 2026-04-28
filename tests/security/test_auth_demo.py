from app.security.auth import verify_supabase_token


def test_demo_user_token_returns_user_principal(monkeypatch):
    monkeypatch.setattr("app.security.auth.settings.DEMO_AUTH_ENABLED", True)

    principal = verify_supabase_token("demo-user-token")

    assert principal.user_id == "demo-user"
    assert principal.email == "demo-user@pazule.demo"
    assert principal.is_admin is False
    assert principal.claims["demo"] is True


def test_demo_admin_token_returns_platform_master(monkeypatch):
    monkeypatch.setattr("app.security.auth.settings.DEMO_AUTH_ENABLED", True)

    principal = verify_supabase_token("demo-admin-token")

    assert principal.user_id == "demo-admin"
    assert principal.email == "demo-admin@pazule.demo"
    assert principal.is_admin is True
    assert principal.claims["app_metadata"]["role"] == "platform_master"
