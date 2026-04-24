from app.core.config import settings


def test_platform_database_settings_are_present():
    assert isinstance(settings.DATABASE_URL, str)
    assert settings.DATABASE_URL
    assert isinstance(settings.SUPABASE_URL, str)
    assert isinstance(settings.SUPABASE_JWKS_URL, str)
    assert settings.SUPABASE_JWT_AUDIENCE == "authenticated"


def test_platform_database_url_helper_uses_settings(monkeypatch):
    from app.db.session import get_database_url

    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite:///tmp/pazule-test.db")

    assert get_database_url() == "sqlite:///tmp/pazule-test.db"
