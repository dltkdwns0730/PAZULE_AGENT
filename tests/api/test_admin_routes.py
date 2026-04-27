from flask import Flask
from unittest.mock import patch

from app.api.routes import api
from app.security.auth import AuthPrincipal


AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


def principal(role: str | None = None) -> AuthPrincipal:
    claims = {"sub": "admin-user"}
    if role:
        claims["app_metadata"] = {"role": role}
    return AuthPrincipal(
        user_id="admin-user",
        email="admin@example.com",
        claims=claims,
    )


def make_client():
    app = Flask(__name__)
    app.register_blueprint(api)
    app.config["TESTING"] = True
    return app.test_client()


def test_admin_summary_requires_admin_role():
    client = make_client()
    with patch("app.api.routes.verify_supabase_token", return_value=principal()):
        response = client.get("/api/admin/summary", headers=AUTH_HEADERS)

    assert response.status_code == 403
    assert response.get_json()["error"] == "admin_required"


def test_admin_summary_returns_metrics_for_admin():
    client = make_client()
    summary = {
        "total_sessions": 1,
        "success_rate": 100,
        "issued_coupons": 1,
        "redeemed_coupons": 0,
        "recent_activity": [],
    }
    with (
        patch("app.api.routes.verify_supabase_token", return_value=principal("admin")),
        patch("app.api.routes.admin_service.get_summary", return_value=summary),
    ):
        response = client.get("/api/admin/summary", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.get_json() == summary


def test_admin_mission_detail_returns_404_for_missing_session():
    client = make_client()
    with (
        patch("app.api.routes.verify_supabase_token", return_value=principal("admin")),
        patch("app.api.routes.admin_service.get_mission_session", return_value=None),
    ):
        response = client.get(
            "/api/admin/mission-sessions/missing", headers=AUTH_HEADERS
        )

    assert response.status_code == 404
    assert response.get_json()["error"] == "mission_session_not_found"


def test_admin_coupon_redeem_uses_admin_console_pos_id():
    client = make_client()
    result = {"redeem_status": "redeemed", "coupon": {"code": "ABC12345"}}
    with (
        patch("app.api.routes.verify_supabase_token", return_value=principal("admin")),
        patch(
            "app.api.routes.admin_service.redeem_coupon", return_value=result
        ) as redeem,
    ):
        response = client.post(
            "/api/admin/coupons/ABC12345/redeem", json={}, headers=AUTH_HEADERS
        )

    assert response.status_code == 200
    redeem.assert_called_once_with("ABC12345", "ADMIN-CONSOLE")
