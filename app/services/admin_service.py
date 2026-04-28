"""Admin operations read models for the PAZULE console."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from app.core.config import settings
from app.db.models import (
    Coupon,
    MissionSession,
    MissionSubmission,
    Organization,
    OrganizationMember,
    Site,
    UserProfile,
)
from app.db.session import session_scope
from app.security.auth import AuthPrincipal
from app.services.coupon_service import coupon_service
from app.services.mission_session_service import mission_session_service


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_dt(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _success(session: dict[str, Any]) -> bool:
    judgment = session.get("latest_judgment") or {}
    return session.get("status") in {"submitted", "coupon_issued"} and (
        judgment.get("success") is True
    )


@dataclass(frozen=True)
class AdminScope:
    """Resolved data visibility for an admin request."""

    principal: AuthPrincipal
    is_platform_master: bool
    organization_ids: tuple[str, ...]

    def can_access_organization(self, organization_id: str | None) -> bool:
        if self.is_platform_master:
            return True
        return bool(organization_id and organization_id in self.organization_ids)


class AdminService:
    """Read-only admin data access with DB and JSON fallback support."""

    def _use_db(self) -> bool:
        return settings.STORAGE_BACKEND.lower() == "db"

    def resolve_scope(self, principal: AuthPrincipal) -> AdminScope:
        if principal.is_admin:
            return AdminScope(
                principal=principal,
                is_platform_master=True,
                organization_ids=(),
            )
        if not self._use_db():
            return AdminScope(
                principal=principal,
                is_platform_master=False,
                organization_ids=(),
            )
        with session_scope() as db:
            rows = db.scalars(
                select(OrganizationMember.organization_id).where(
                    OrganizationMember.user_id == principal.user_id,
                    OrganizationMember.role.in_(["owner", "manager", "viewer"]),
                )
            ).all()
        return AdminScope(
            principal=principal,
            is_platform_master=False,
            organization_ids=tuple(rows),
        )

    def list_organizations(self, scope: AdminScope) -> list[dict[str, Any]]:
        if not self._use_db():
            if scope.is_platform_master:
                return [{"id": "pazule-default", "name": "PAZULE", "slug": "pazule"}]
            return []
        with session_scope() as db:
            stmt = select(Organization).order_by(Organization.name.asc())
            if not scope.is_platform_master:
                if not scope.organization_ids:
                    return []
                stmt = stmt.where(Organization.id.in_(scope.organization_ids))
            rows = db.scalars(stmt).all()
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "slug": row.slug,
                    "created_at": _iso(row.created_at),
                }
                for row in rows
            ]

    def get_summary(
        self, scope: AdminScope, organization_id: str | None = None
    ) -> dict[str, Any]:
        if self._use_db():
            return self._db_summary(scope, organization_id=organization_id)
        sessions = self._filter_json_sessions(
            self._json_sessions(), scope, organization_id=organization_id
        )
        coupons = self._json_coupons()
        session_ids = {row.get("mission_id") for row in sessions}
        coupons = [
            row
            for row in coupons
            if not row.get("mission_id") or row.get("mission_id") in session_ids
        ]
        successful = [row for row in sessions if _success(row)]
        recent = sorted(
            sessions, key=lambda row: _parse_dt(row.get("created_at")), reverse=True
        )[:5]
        return {
            "total_sessions": len(sessions),
            "success_rate": round((len(successful) / len(sessions)) * 100, 1)
            if sessions
            else 0,
            "issued_coupons": len(coupons),
            "redeemed_coupons": len(
                [row for row in coupons if row.get("status") == "redeemed"]
            ),
            "recent_activity": recent,
        }

    def list_mission_sessions(
        self,
        scope: AdminScope,
        status: str | None = None,
        search: str | None = None,
        organization_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._use_db():
            return self._db_mission_sessions(
                scope=scope,
                status=status,
                search=search,
                organization_id=organization_id,
            )
        rows = self._filter_json_sessions(
            self._json_sessions(), scope, organization_id=organization_id
        )
        if status:
            rows = [row for row in rows if row.get("status") == status]
        if search:
            term = search.lower()
            rows = [
                row
                for row in rows
                if term
                in " ".join(
                    str(row.get(key, ""))
                    for key in ["mission_id", "user_id", "answer", "mission_type"]
                ).lower()
            ]
        return sorted(
            rows, key=lambda row: _parse_dt(row.get("created_at")), reverse=True
        )

    def get_mission_session(
        self, scope: AdminScope, mission_id: str
    ) -> dict[str, Any] | None:
        if self._use_db():
            with session_scope() as db:
                model = db.scalar(
                    select(MissionSession)
                    .where(
                        (MissionSession.legacy_mission_id == mission_id)
                        | (MissionSession.id == mission_id)
                    )
                    .limit(1)
                )
                if not model:
                    return None
                site = db.get(Site, model.site_id)
                if not scope.can_access_organization(
                    site.organization_id if site else None
                ):
                    return None
                submissions = db.scalars(
                    select(MissionSubmission)
                    .where(MissionSubmission.mission_session_id == model.id)
                    .order_by(MissionSubmission.submitted_at.asc())
                ).all()
                return self._session_to_dict(model, submissions=submissions)
        row = mission_session_service.get_session(mission_id)
        if not row:
            return None
        if not self._filter_json_sessions([row], scope):
            return None
        return row

    def list_coupons(
        self,
        scope: AdminScope,
        status: str | None = None,
        search: str | None = None,
        organization_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._use_db():
            return self._db_coupons(
                scope=scope,
                status=status,
                search=search,
                organization_id=organization_id,
            )
        rows = self._json_coupons()
        allowed_sessions = self._filter_json_sessions(
            self._json_sessions(), scope, organization_id=organization_id
        )
        allowed_session_ids = {row.get("mission_id") for row in allowed_sessions}
        rows = [
            row
            for row in rows
            if not row.get("mission_id") or row.get("mission_id") in allowed_session_ids
        ]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        if search:
            term = search.lower()
            rows = [
                row
                for row in rows
                if term
                in " ".join(
                    str(row.get(key, ""))
                    for key in ["code", "user_id", "answer", "status"]
                ).lower()
            ]
        return sorted(
            rows, key=lambda row: _parse_dt(row.get("issued_at")), reverse=True
        )

    def redeem_coupon(
        self, scope: AdminScope, code: str, partner_pos_id: str
    ) -> dict[str, Any]:
        if not self._can_access_coupon(scope, code):
            return {
                "redeem_status": "forbidden",
                "message": "Coupon is outside admin scope.",
            }
        return coupon_service.redeem_coupon(code, partner_pos_id)

    def list_users(
        self,
        scope: AdminScope,
        search: str | None = None,
        organization_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._use_db():
            return self._db_users(
                scope=scope,
                search=search,
                organization_id=organization_id,
            )
        sessions = self._filter_json_sessions(
            self._json_sessions(), scope, organization_id=organization_id
        )
        coupons = self._json_coupons()
        users: dict[str, dict[str, Any]] = {}
        for row in sessions:
            user_id = row.get("user_id") or "unknown"
            users.setdefault(
                user_id,
                {
                    "user_id": user_id,
                    "email": None,
                    "total_sessions": 0,
                    "total_coupons": 0,
                },
            )
            users[user_id]["total_sessions"] += 1
        for row in coupons:
            user_id = row.get("user_id") or "unknown"
            users.setdefault(
                user_id,
                {
                    "user_id": user_id,
                    "email": None,
                    "total_sessions": 0,
                    "total_coupons": 0,
                },
            )
            users[user_id]["total_coupons"] += 1
        rows = list(users.values())
        if search:
            term = search.lower()
            rows = [
                row
                for row in rows
                if term in f"{row.get('user_id')} {row.get('email') or ''}".lower()
            ]
        return sorted(rows, key=lambda row: row["total_sessions"], reverse=True)

    def _json_sessions(self) -> list[dict[str, Any]]:
        return mission_session_service._read_all().get("sessions", [])

    def _json_coupons(self) -> list[dict[str, Any]]:
        return coupon_service._read_all().get("coupons", [])

    def _filter_json_sessions(
        self,
        rows: list[dict[str, Any]],
        scope: AdminScope,
        organization_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if scope.is_platform_master:
            return rows
        if organization_id and not scope.can_access_organization(organization_id):
            return []
        # JSON fallback has no organization table, so non-master org admins cannot
        # be safely granted broad visibility there.
        return []

    def _site_ids_for_scope(
        self, db, scope: AdminScope, organization_id: str | None = None
    ) -> list[str] | None:
        if organization_id and not scope.can_access_organization(organization_id):
            return []
        if scope.is_platform_master and not organization_id:
            return None
        organization_ids = (
            [organization_id] if organization_id else list(scope.organization_ids)
        )
        if not organization_ids:
            return []
        return list(
            db.scalars(
                select(Site.id).where(Site.organization_id.in_(organization_ids))
            )
        )

    def _apply_session_scope(
        self, db, stmt, scope: AdminScope, organization_id: str | None
    ):
        site_ids = self._site_ids_for_scope(db, scope, organization_id=organization_id)
        if site_ids is None:
            return stmt
        if not site_ids:
            return stmt.where(False)
        return stmt.where(MissionSession.site_id.in_(site_ids))

    def _can_access_coupon(self, scope: AdminScope, code: str) -> bool:
        if scope.is_platform_master:
            return True
        if not self._use_db() or not scope.organization_ids:
            return False
        with session_scope() as db:
            coupon = db.scalar(select(Coupon).where(Coupon.code == code).limit(1))
            if not coupon or not coupon.mission_session_id:
                return False
            session = db.get(MissionSession, coupon.mission_session_id)
            if not session:
                return False
            site = db.get(Site, session.site_id)
            return scope.can_access_organization(site.organization_id if site else None)

    def _db_summary(
        self, scope: AdminScope, organization_id: str | None = None
    ) -> dict[str, Any]:
        with session_scope() as db:
            scoped_sessions = self._apply_session_scope(
                db, select(MissionSession), scope, organization_id
            )
            scoped_coupon_stmt = select(Coupon).join(
                MissionSession, Coupon.mission_session_id == MissionSession.id
            )
            scoped_coupon_stmt = self._apply_session_scope(
                db, scoped_coupon_stmt, scope, organization_id
            )
            total_sessions = (
                db.scalar(
                    scoped_sessions.with_only_columns(func.count()).order_by(None)
                )
                or 0
            )
            issued_coupons = (
                db.scalar(
                    scoped_coupon_stmt.with_only_columns(func.count()).order_by(None)
                )
                or 0
            )
            redeemed_coupons = (
                db.scalar(
                    scoped_coupon_stmt.where(Coupon.status == "redeemed")
                    .with_only_columns(func.count())
                    .order_by(None)
                )
                or 0
            )
            rows = db.scalars(
                self._apply_session_scope(
                    db,
                    select(MissionSession).order_by(MissionSession.created_at.desc()),
                    scope,
                    organization_id,
                ).limit(5)
            ).all()
            all_rows = db.scalars(scoped_sessions).all()
            successful = [row for row in all_rows if self._session_success(row)]
            return {
                "total_sessions": int(total_sessions),
                "success_rate": round((len(successful) / len(all_rows)) * 100, 1)
                if all_rows
                else 0,
                "issued_coupons": int(issued_coupons),
                "redeemed_coupons": int(redeemed_coupons),
                "recent_activity": [self._session_to_dict(row) for row in rows],
            }

    def _db_mission_sessions(
        self,
        scope: AdminScope,
        status: str | None = None,
        search: str | None = None,
        organization_id: str | None = None,
    ) -> list[dict[str, Any]]:
        with session_scope() as db:
            stmt = select(MissionSession).order_by(MissionSession.created_at.desc())
            stmt = self._apply_session_scope(db, stmt, scope, organization_id)
            if status:
                stmt = stmt.where(MissionSession.status == status)
            rows = db.scalars(stmt).all()
            result = [self._session_to_dict(row) for row in rows]
        if search:
            term = search.lower()
            result = [
                row
                for row in result
                if term
                in " ".join(
                    str(row.get(key, ""))
                    for key in ["mission_id", "user_id", "answer", "mission_type"]
                ).lower()
            ]
        return result

    def _db_coupons(
        self,
        scope: AdminScope,
        status: str | None = None,
        search: str | None = None,
        organization_id: str | None = None,
    ) -> list[dict[str, Any]]:
        with session_scope() as db:
            stmt = (
                select(Coupon)
                .join(MissionSession, Coupon.mission_session_id == MissionSession.id)
                .order_by(Coupon.issued_at.desc())
            )
            stmt = self._apply_session_scope(db, stmt, scope, organization_id)
            if status:
                stmt = stmt.where(Coupon.status == status)
            rows = db.scalars(stmt).all()
            result = [self._coupon_to_dict(row) for row in rows]
        if search:
            term = search.lower()
            result = [
                row
                for row in result
                if term
                in " ".join(
                    str(row.get(key, ""))
                    for key in ["code", "user_id", "answer", "status"]
                ).lower()
            ]
        return result

    def _db_users(
        self,
        scope: AdminScope,
        search: str | None = None,
        organization_id: str | None = None,
    ) -> list[dict[str, Any]]:
        with session_scope() as db:
            session_stmt = self._apply_session_scope(
                db, select(MissionSession), scope, organization_id
            )
            sessions = db.scalars(session_stmt).all()
            user_ids = sorted({row.user_id for row in sessions})
            if not user_ids:
                return []
            profiles = db.scalars(
                select(UserProfile).where(UserProfile.id.in_(user_ids))
            ).all()
            result = []
            for profile in profiles:
                session_count = (
                    db.scalar(
                        session_stmt.where(MissionSession.user_id == profile.id)
                        .with_only_columns(func.count())
                        .order_by(None)
                    )
                    or 0
                )
                coupon_count = (
                    db.scalar(
                        select(Coupon)
                        .join(
                            MissionSession,
                            Coupon.mission_session_id == MissionSession.id,
                        )
                        .where(Coupon.user_id == profile.id)
                        .where(MissionSession.id.in_([row.id for row in sessions]))
                        .with_only_columns(func.count())
                    )
                    or 0
                )
                result.append(
                    {
                        "user_id": profile.id,
                        "email": profile.email,
                        "display_name": profile.display_name,
                        "total_sessions": int(session_count),
                        "total_coupons": int(coupon_count),
                    }
                )
        if search:
            term = search.lower()
            result = [
                row
                for row in result
                if term
                in f"{row.get('user_id')} {row.get('email') or ''} {row.get('display_name') or ''}".lower()
            ]
        return sorted(result, key=lambda row: row["total_sessions"], reverse=True)

    def _session_success(self, model: MissionSession) -> bool:
        return (
            model.status in {"submitted", "coupon_issued"}
            and (model.latest_judgment or {}).get("success") is True
        )

    def _session_to_dict(
        self,
        model: MissionSession,
        submissions: list[MissionSubmission] | None = None,
    ) -> dict[str, Any]:
        return {
            "mission_id": model.legacy_mission_id or model.id,
            "user_id": model.user_id,
            "site_id": model.site_id,
            "mission_type": model.mission_type,
            "answer": model.answer,
            "hint": model.hint,
            "status": model.status,
            "created_at": _iso(model.created_at),
            "expires_at": _iso(model.expires_at),
            "max_submissions": model.max_submissions,
            "latest_judgment": model.latest_judgment,
            "coupon_code": model.coupon_code,
            "submissions": [
                {
                    "submitted_at": _iso(row.submitted_at),
                    "image_hash": row.image_hash,
                    "result_summary": row.result_summary,
                }
                for row in (submissions or [])
            ],
        }

    def _coupon_to_dict(self, model: Coupon) -> dict[str, Any]:
        return {
            "code": model.code,
            "description": model.description,
            "mission_type": model.mission_type,
            "answer": model.answer,
            "mission_id": model.mission_session_id,
            "user_id": model.user_id,
            "partner_id": model.partner_id,
            "discount_rule": model.discount_rule,
            "status": model.status,
            "issued_at": _iso(model.issued_at),
            "expires_at": _iso(model.expires_at),
            "redeemed_at": _iso(model.redeemed_at),
            "partner_pos_id": model.partner_pos_id,
        }


admin_service = AdminService()
