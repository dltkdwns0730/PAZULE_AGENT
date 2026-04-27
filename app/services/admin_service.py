"""Admin operations read models for the PAZULE console."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from app.core.config import settings
from app.db.models import Coupon, MissionSession, MissionSubmission, UserProfile
from app.db.session import session_scope
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


class AdminService:
    """Read-only admin data access with DB and JSON fallback support."""

    def _use_db(self) -> bool:
        return settings.STORAGE_BACKEND.lower() == "db"

    def get_summary(self) -> dict[str, Any]:
        if self._use_db():
            return self._db_summary()
        sessions = self._json_sessions()
        coupons = self._json_coupons()
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
        self, status: str | None = None, search: str | None = None
    ) -> list[dict[str, Any]]:
        if self._use_db():
            return self._db_mission_sessions(status=status, search=search)
        rows = self._json_sessions()
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

    def get_mission_session(self, mission_id: str) -> dict[str, Any] | None:
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
                submissions = db.scalars(
                    select(MissionSubmission)
                    .where(MissionSubmission.mission_session_id == model.id)
                    .order_by(MissionSubmission.submitted_at.asc())
                ).all()
                return self._session_to_dict(model, submissions=submissions)
        return mission_session_service.get_session(mission_id)

    def list_coupons(
        self, status: str | None = None, search: str | None = None
    ) -> list[dict[str, Any]]:
        if self._use_db():
            return self._db_coupons(status=status, search=search)
        rows = self._json_coupons()
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

    def redeem_coupon(self, code: str, partner_pos_id: str) -> dict[str, Any]:
        return coupon_service.redeem_coupon(code, partner_pos_id)

    def list_users(self, search: str | None = None) -> list[dict[str, Any]]:
        if self._use_db():
            return self._db_users(search=search)
        sessions = self._json_sessions()
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

    def _db_summary(self) -> dict[str, Any]:
        with session_scope() as db:
            total_sessions = (
                db.scalar(select(func.count()).select_from(MissionSession)) or 0
            )
            issued_coupons = db.scalar(select(func.count()).select_from(Coupon)) or 0
            redeemed_coupons = (
                db.scalar(select(func.count()).where(Coupon.status == "redeemed")) or 0
            )
            rows = db.scalars(
                select(MissionSession)
                .order_by(MissionSession.created_at.desc())
                .limit(5)
            ).all()
            all_rows = db.scalars(select(MissionSession)).all()
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
        self, status: str | None = None, search: str | None = None
    ) -> list[dict[str, Any]]:
        with session_scope() as db:
            stmt = select(MissionSession).order_by(MissionSession.created_at.desc())
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
        self, status: str | None = None, search: str | None = None
    ) -> list[dict[str, Any]]:
        with session_scope() as db:
            stmt = select(Coupon).order_by(Coupon.issued_at.desc())
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

    def _db_users(self, search: str | None = None) -> list[dict[str, Any]]:
        with session_scope() as db:
            profiles = db.scalars(select(UserProfile)).all()
            result = []
            for profile in profiles:
                session_count = (
                    db.scalar(
                        select(func.count()).where(MissionSession.user_id == profile.id)
                    )
                    or 0
                )
                coupon_count = (
                    db.scalar(select(func.count()).where(Coupon.user_id == profile.id))
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
