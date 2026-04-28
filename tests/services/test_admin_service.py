from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine

from app.db.models import (
    Base,
    Coupon,
    MissionSession,
    Organization,
    OrganizationMember,
    Site,
    UserProfile,
)
from app.db.session import session_scope
from app.security.auth import AuthPrincipal
from app.services.admin_service import AdminService


def _principal(user_id: str, role: str | None = None) -> AuthPrincipal:
    claims = {"sub": user_id}
    if role:
        claims["app_metadata"] = {"role": role}
    return AuthPrincipal(user_id=user_id, email=f"{user_id}@example.com", claims=claims)


def _database_url(tmp_path) -> str:
    path = tmp_path / "admin-service.db"
    url = f"sqlite:///{path}"
    engine = create_engine(url, future=True)
    Base.metadata.create_all(engine)
    engine.dispose()
    return url


def _seed_multi_company_data(database_url: str) -> None:
    now = datetime.now(timezone.utc)
    with session_scope(database_url) as db:
        db.add_all(
            [
                Organization(id="org-a", name="Company A", slug="company-a"),
                Organization(id="org-b", name="Company B", slug="company-b"),
                UserProfile(
                    id="admin-a", display_name="Admin A", email="a@example.com"
                ),
                UserProfile(id="user-a", display_name="User A", email="ua@example.com"),
                UserProfile(id="user-b", display_name="User B", email="ub@example.com"),
                OrganizationMember(
                    id="member-a",
                    organization_id="org-a",
                    user_id="admin-a",
                    role="owner",
                ),
                Site(
                    id="site-a",
                    organization_id="org-a",
                    slug="site-a",
                    name="Site A",
                    latitude=37.0,
                    longitude=126.0,
                    radius_meters=300,
                    is_active=True,
                ),
                Site(
                    id="site-b",
                    organization_id="org-b",
                    slug="site-b",
                    name="Site B",
                    latitude=37.1,
                    longitude=126.1,
                    radius_meters=300,
                    is_active=True,
                ),
                MissionSession(
                    id="session-a",
                    legacy_mission_id="legacy-a",
                    user_id="user-a",
                    site_id="site-a",
                    mission_type="location",
                    answer="answer-a",
                    hint="hint-a",
                    status="coupon_issued",
                    latest_judgment={"success": True},
                    created_at=now,
                    expires_at=now + timedelta(minutes=30),
                ),
                MissionSession(
                    id="session-b",
                    legacy_mission_id="legacy-b",
                    user_id="user-b",
                    site_id="site-b",
                    mission_type="atmosphere",
                    answer="answer-b",
                    hint="hint-b",
                    status="coupon_issued",
                    latest_judgment={"success": True},
                    created_at=now,
                    expires_at=now + timedelta(minutes=30),
                ),
                Coupon(
                    id="coupon-a",
                    code="COUPONA1",
                    mission_session_id="session-a",
                    user_id="user-a",
                    status="issued",
                    description="coupon a",
                    mission_type="mission1",
                    answer="answer-a",
                    discount_rule="10%",
                    issued_at=now,
                    expires_at=now + timedelta(days=7),
                ),
                Coupon(
                    id="coupon-b",
                    code="COUPONB1",
                    mission_session_id="session-b",
                    user_id="user-b",
                    status="issued",
                    description="coupon b",
                    mission_type="mission2",
                    answer="answer-b",
                    discount_rule="10%",
                    issued_at=now,
                    expires_at=now + timedelta(days=7),
                ),
            ]
        )


def _use_admin_db(monkeypatch, database_url: str) -> None:
    monkeypatch.setattr(
        "app.services.admin_service.settings.DATABASE_URL", database_url
    )
    monkeypatch.setattr("app.services.admin_service.settings.STORAGE_BACKEND", "db")


def test_org_admin_scope_limits_activity_to_own_company(tmp_path, monkeypatch):
    database_url = _database_url(tmp_path)
    _seed_multi_company_data(database_url)
    _use_admin_db(monkeypatch, database_url)

    service = AdminService()
    scope = service.resolve_scope(_principal("admin-a"))

    assert scope.organization_ids == ("org-a",)
    assert service.list_organizations(scope)[0]["id"] == "org-a"
    assert [row["mission_id"] for row in service.list_mission_sessions(scope)] == [
        "legacy-a"
    ]
    assert [row["code"] for row in service.list_coupons(scope)] == ["COUPONA1"]
    assert [row["user_id"] for row in service.list_users(scope)] == ["user-a"]
    assert service.redeem_coupon(scope, "COUPONB1", "POS-1")["redeem_status"] == (
        "forbidden"
    )


def test_platform_master_can_view_all_companies(tmp_path, monkeypatch):
    database_url = _database_url(tmp_path)
    _seed_multi_company_data(database_url)
    _use_admin_db(monkeypatch, database_url)

    service = AdminService()
    scope = service.resolve_scope(_principal("master", "platform_master"))

    assert scope.is_platform_master is True
    assert {row["id"] for row in service.list_organizations(scope)} == {
        "org-a",
        "org-b",
    }
    assert {row["mission_id"] for row in service.list_mission_sessions(scope)} == {
        "legacy-a",
        "legacy-b",
    }
