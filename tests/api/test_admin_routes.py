from flask import Flask
from unittest.mock import patch

from app.api.admin_routes import admin_api
from app.security.auth import AuthPrincipal
from app.services.admin_service import AdminScope


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


def scope(role: str = "admin", organization_ids: tuple[str, ...] = ()) -> AdminScope:
    return AdminScope(
        principal=principal(role if role in {"admin", "platform_master"} else None),
        is_platform_master=role in {"admin", "platform_master"},
        organization_ids=organization_ids,
    )


def make_client():
    app = Flask(__name__)
    app.register_blueprint(admin_api)
    app.config["TESTING"] = True
    return app.test_client()


def test_admin_summary_requires_admin_role():
    client = make_client()
    with (
        patch("app.api.admin_routes.verify_supabase_token", return_value=principal()),
        patch(
            "app.api.admin_routes.admin_service.resolve_scope",
            return_value=scope("org_admin", ()),
        ),
    ):
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
        patch(
            "app.api.admin_routes.verify_supabase_token",
            return_value=principal("admin"),
        ),
        patch(
            "app.api.admin_routes.admin_service.resolve_scope",
            return_value=scope("admin"),
        ),
        patch("app.api.admin_routes.admin_service.get_summary", return_value=summary),
    ):
        response = client.get("/api/admin/summary", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.get_json() == summary


def test_admin_summary_passes_organization_filter_for_org_admin():
    client = make_client()
    summary = {
        "total_sessions": 1,
        "success_rate": 100,
        "issued_coupons": 1,
        "redeemed_coupons": 0,
        "recent_activity": [],
    }
    org_scope = scope("org_admin", ("org-1",))
    with (
        patch("app.api.admin_routes.verify_supabase_token", return_value=principal()),
        patch(
            "app.api.admin_routes.admin_service.resolve_scope", return_value=org_scope
        ),
        patch(
            "app.api.admin_routes.admin_service.get_summary", return_value=summary
        ) as get_summary,
    ):
        response = client.get(
            "/api/admin/summary?organization_id=org-1", headers=AUTH_HEADERS
        )

    assert response.status_code == 200
    get_summary.assert_called_once_with(org_scope, organization_id="org-1")


def test_admin_organizations_returns_visible_companies():
    client = make_client()
    org_scope = scope("org_admin", ("org-1",))
    organizations = [{"id": "org-1", "name": "Company A", "slug": "company-a"}]
    with (
        patch("app.api.admin_routes.verify_supabase_token", return_value=principal()),
        patch(
            "app.api.admin_routes.admin_service.resolve_scope", return_value=org_scope
        ),
        patch(
            "app.api.admin_routes.admin_service.list_organizations",
            return_value=organizations,
        ) as list_organizations,
    ):
        response = client.get("/api/admin/organizations", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.get_json() == organizations
    list_organizations.assert_called_once_with(org_scope)


def test_admin_mission_detail_returns_404_for_missing_session():
    client = make_client()
    with (
        patch(
            "app.api.admin_routes.verify_supabase_token",
            return_value=principal("admin"),
        ),
        patch(
            "app.api.admin_routes.admin_service.resolve_scope",
            return_value=scope("admin"),
        ),
        patch(
            "app.api.admin_routes.admin_service.get_mission_session", return_value=None
        ),
    ):
        response = client.get(
            "/api/admin/mission-sessions/missing", headers=AUTH_HEADERS
        )

    assert response.status_code == 404
    assert response.get_json()["error"] == "mission_session_not_found"


def test_admin_coupon_redeem_uses_admin_console_pos_id():
    client = make_client()
    result = {"redeem_status": "redeemed", "coupon": {"code": "ABC12345"}}
    admin_scope = scope("admin")
    with (
        patch(
            "app.api.admin_routes.verify_supabase_token",
            return_value=principal("admin"),
        ),
        patch(
            "app.api.admin_routes.admin_service.resolve_scope",
            return_value=admin_scope,
        ),
        patch(
            "app.api.admin_routes.admin_service.redeem_coupon", return_value=result
        ) as redeem,
    ):
        response = client.post(
            "/api/admin/coupons/ABC12345/redeem", json={}, headers=AUTH_HEADERS
        )

    assert response.status_code == 200
    redeem.assert_called_once_with(admin_scope, "ABC12345", "ADMIN-CONSOLE")
