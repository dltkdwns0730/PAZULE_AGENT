"""DB-backed repositories for mission sessions and coupons."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select

from app.core.config import constants, settings
from app.core.utils import normalize_mission_type
from app.db.models import (
    Coupon,
    CouponStatus,
    MissionEvent,
    MissionSession,
    MissionSessionStatus,
    MissionSubmission,
    Organization,
    Site,
    UserProfile,
)
from app.db.session import session_scope


DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _ensure_user_profile(db, user_id: str) -> None:
    if db.get(UserProfile, user_id):
        return
    db.add(UserProfile(id=user_id, display_name=user_id, email=None))


def _ensure_site(db, site_id: str) -> None:
    if db.get(Site, site_id):
        return
    if not db.get(Organization, DEFAULT_ORG_ID):
        db.add(
            Organization(
                id=DEFAULT_ORG_ID,
                name="PAZULE",
                slug="pazule",
            )
        )
    db.add(
        Site(
            id=site_id,
            organization_id=DEFAULT_ORG_ID,
            slug=site_id,
            name=site_id,
            latitude=settings.MISSION_SITE_LAT,
            longitude=settings.MISSION_SITE_LON,
            radius_meters=settings.MISSION_SITE_RADIUS_METERS,
            is_active=True,
        )
    )


class MissionSessionRepository:
    """SQLAlchemy implementation of mission session persistence."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def create_session(
        self,
        user_id: str,
        site_id: str,
        mission_type: str,
        answer: str,
        hint: str,
    ) -> dict[str, Any]:
        now = _utcnow()
        legacy_mission_id = str(uuid4())
        normalized_type = normalize_mission_type(mission_type)
        final_user_id = user_id or "guest"
        final_site_id = site_id or "pazule-default"
        expires_at = now + timedelta(minutes=settings.MISSION_SESSION_TTL_MINUTES)

        with session_scope(self.database_url) as db:
            _ensure_user_profile(db, final_user_id)
            _ensure_site(db, final_site_id)
            model = MissionSession(
                id=str(uuid4()),
                legacy_mission_id=legacy_mission_id,
                user_id=final_user_id,
                site_id=final_site_id,
                mission_type=normalized_type,
                answer=answer,
                hint=hint,
                status=MissionSessionStatus.CREATED.value,
                max_submissions=settings.MISSION_MAX_SUBMISSIONS,
                latest_judgment=None,
                created_at=now,
                expires_at=expires_at,
            )
            db.add(model)
            db.flush()
            return self._to_dict(db, model)

    def get_session(self, mission_id: str) -> dict[str, Any] | None:
        with session_scope(self.database_url) as db:
            model = self._find_session(db, mission_id)
            if not model:
                return None
            return self._to_dict(db, model)

    def can_submit(self, mission_id: str) -> tuple[bool, str]:
        with session_scope(self.database_url) as db:
            model = self._find_session(db, mission_id)
            if not model:
                return False, "session_not_found"
            if _utcnow() > _as_aware(model.expires_at):
                return False, "session_expired"
            submission_count = self._submission_count(db, model.id)
            if submission_count >= model.max_submissions:
                return False, "submission_limit_reached"
            return True, "ok"

    def record_submission(
        self, mission_id: str, image_hash: str, result: dict[str, Any]
    ) -> dict[str, Any] | None:
        with session_scope(self.database_url) as db:
            model = self._find_session(db, mission_id)
            if not model:
                return None
            db.add(
                MissionSubmission(
                    id=str(uuid4()),
                    mission_session_id=model.id,
                    image_hash=image_hash,
                    result_summary={
                        "success": bool(result.get("success")),
                        "confidence": result.get("confidence"),
                    },
                    submitted_at=_utcnow(),
                )
            )
            model.status = MissionSessionStatus.SUBMITTED.value
            model.latest_judgment = result
            db.flush()
            return self._to_dict(db, model)

    def mark_coupon_issued(
        self, mission_id: str, coupon_code: str
    ) -> dict[str, Any] | None:
        with session_scope(self.database_url) as db:
            model = self._find_session(db, mission_id)
            if not model:
                return None
            model.coupon_code = coupon_code
            model.status = MissionSessionStatus.COUPON_ISSUED.value
            db.flush()
            return self._to_dict(db, model)

    def is_mission_completed_today(self, user_id: str, mission_type: str) -> bool:
        today = _utcnow().date()
        normalized_type = normalize_mission_type(mission_type)
        with session_scope(self.database_url) as db:
            rows = db.scalars(
                select(MissionSession).where(
                    MissionSession.user_id == user_id,
                    MissionSession.mission_type == normalized_type,
                    MissionSession.status.in_(
                        [
                            MissionSessionStatus.SUBMITTED.value,
                            MissionSessionStatus.COUPON_ISSUED.value,
                        ]
                    ),
                )
            ).all()
            for row in rows:
                if _as_aware(row.created_at).date() != today:
                    continue
                if (row.latest_judgment or {}).get("success") is True:
                    return True
            return False

    def is_duplicate_hash_for_user(self, user_id: str, image_hash: str) -> bool:
        if not image_hash:
            return False
        with session_scope(self.database_url) as db:
            exists = db.scalar(
                select(MissionSubmission.id)
                .join(MissionSession)
                .where(
                    MissionSession.user_id == user_id,
                    MissionSubmission.image_hash == image_hash,
                )
                .limit(1)
            )
            return exists is not None

    def get_user_stats(self, user_id: str) -> dict[str, Any]:
        with session_scope(self.database_url) as db:
            rows = db.scalars(
                select(MissionSession)
                .where(MissionSession.user_id == user_id)
                .order_by(MissionSession.created_at.desc())
            ).all()
            stats: dict[str, Any] = {
                "total_attempts": len(rows),
                "success_location": 0,
                "success_atmosphere": 0,
                "total_coupons": 0,
                "history": [],
            }
            for row in rows:
                success = (
                    row.status
                    in [
                        MissionSessionStatus.SUBMITTED.value,
                        MissionSessionStatus.COUPON_ISSUED.value,
                    ]
                    and (row.latest_judgment or {}).get("success") is True
                )
                if not success:
                    continue
                if row.mission_type == "location":
                    stats["success_location"] += 1
                elif row.mission_type == "atmosphere":
                    stats["success_atmosphere"] += 1
                if row.coupon_code:
                    stats["total_coupons"] += 1
                stats["history"].append(
                    {
                        "mission_id": row.legacy_mission_id or row.id,
                        "mission_type": row.mission_type,
                        "answer": row.answer,
                        "completed_at": _iso(row.created_at),
                    }
                )
            stats["history"] = stats["history"][:5]
            return stats

    def reset_user_history(self, user_id: str) -> None:
        with session_scope(self.database_url) as db:
            rows = db.scalars(
                select(MissionSession).where(MissionSession.user_id == user_id)
            ).all()
            session_ids = [row.id for row in rows]
            submissions = db.scalars(
                select(MissionSubmission).where(
                    MissionSubmission.mission_session_id.in_(session_ids)
                )
            ).all()
            coupons = db.scalars(
                select(Coupon).where(Coupon.mission_session_id.in_(session_ids))
            ).all()
            events = db.scalars(
                select(MissionEvent).where(
                    MissionEvent.mission_session_id.in_(session_ids)
                )
            ).all()
            for row in [*submissions, *coupons, *events, *rows]:
                db.delete(row)

    def _find_session(self, db, mission_id: str) -> MissionSession | None:
        return db.scalar(
            select(MissionSession)
            .where(
                (MissionSession.legacy_mission_id == mission_id)
                | (MissionSession.id == mission_id)
            )
            .limit(1)
        )

    def _submission_count(self, db, session_id: str) -> int:
        return int(
            db.scalar(
                select(func.count())
                .select_from(MissionSubmission)
                .where(MissionSubmission.mission_session_id == session_id)
            )
            or 0
        )

    def _to_dict(self, db, model: MissionSession) -> dict[str, Any]:
        submissions = db.scalars(
            select(MissionSubmission)
            .where(MissionSubmission.mission_session_id == model.id)
            .order_by(MissionSubmission.submitted_at.asc())
        ).all()
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
            "submissions": [
                {
                    "submitted_at": _iso(sub.submitted_at),
                    "image_hash": sub.image_hash,
                    "result_summary": sub.result_summary,
                }
                for sub in submissions
            ],
            "latest_judgment": model.latest_judgment,
            "coupon_code": model.coupon_code,
        }


class CouponRepository:
    """SQLAlchemy implementation of coupon persistence."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def has_coupon_for_answer(self, user_id: str, answer: str) -> bool:
        with session_scope(self.database_url) as db:
            return self._find_by_user_and_answer(db, user_id, answer) is not None

    def issue_coupon(
        self,
        mission_type: str,
        answer: str,
        mission_id: str | None = None,
        user_id: str = "guest",
        partner_id: str | None = None,
        discount_rule: str = constants.DEFAULT_DISCOUNT_RULE,
        code_factory: Callable[[], str] | None = None,
    ) -> dict[str, Any]:
        with session_scope(self.database_url) as db:
            _ensure_user_profile(db, user_id)
            mission_session = None
            if mission_id:
                mission_session = self._find_session(db, mission_id)
                if mission_session:
                    existing = self._find_by_session_id(db, mission_session.id)
                    if existing:
                        return self._to_dict(db, existing)

            existing = self._find_by_user_and_answer(db, user_id, answer)
            if existing:
                return self._to_dict(db, existing)

            issued_at = _utcnow()
            expires_at = issued_at + timedelta(days=7)
            description = (
                f"{answer} location mission coupon"
                if mission_type == "mission1"
                else f"{answer} atmosphere mission coupon"
            )
            code = self._new_unique_code(db, code_factory or (lambda: str(uuid4())[:8]))
            model = Coupon(
                id=str(uuid4()),
                code=code,
                mission_session_id=mission_session.id if mission_session else None,
                user_id=user_id,
                status=CouponStatus.ISSUED.value,
                description=description,
                mission_type=mission_type,
                answer=answer,
                partner_id=partner_id,
                discount_rule=discount_rule,
                issued_at=issued_at,
                expires_at=expires_at,
                redeemed_at=None,
                partner_pos_id=None,
            )
            db.add(model)
            if mission_session:
                mission_session.status = MissionSessionStatus.COUPON_ISSUED.value
                mission_session.coupon_code = code
            db.flush()
            return self._to_dict(db, model)

    def redeem_coupon(self, code: str, partner_pos_id: str) -> dict[str, Any]:
        with session_scope(self.database_url) as db:
            model = db.scalar(select(Coupon).where(Coupon.code == code).limit(1))
            if not model:
                return {"redeem_status": "not_found", "message": "Coupon not found."}
            coupon = self._to_dict(db, model)
            if model.status == CouponStatus.REDEEMED.value:
                return {
                    "redeem_status": "already_redeemed",
                    "message": "Coupon already redeemed.",
                    "coupon": coupon,
                }
            if _utcnow() > _as_aware(model.expires_at):
                model.status = CouponStatus.EXPIRED.value
                db.flush()
                return {
                    "redeem_status": "expired",
                    "message": "Coupon expired.",
                    "coupon": self._to_dict(db, model),
                }
            model.status = CouponStatus.REDEEMED.value
            model.redeemed_at = _utcnow()
            model.partner_pos_id = partner_pos_id
            db.flush()
            return {
                "redeem_status": "redeemed",
                "message": "Coupon redeemed.",
                "coupon": self._to_dict(db, model),
            }

    def get_user_coupons(self, user_id: str) -> list[dict[str, Any]]:
        with session_scope(self.database_url) as db:
            rows = db.scalars(
                select(Coupon)
                .where(Coupon.user_id == user_id)
                .order_by(Coupon.issued_at.desc())
            ).all()
            return [self._to_dict(db, row) for row in rows]

    def reset_user_coupons(self, user_id: str) -> None:
        with session_scope(self.database_url) as db:
            rows = db.scalars(select(Coupon).where(Coupon.user_id == user_id)).all()
            for row in rows:
                db.delete(row)

    def _find_session(self, db, mission_id: str) -> MissionSession | None:
        return db.scalar(
            select(MissionSession)
            .where(
                (MissionSession.legacy_mission_id == mission_id)
                | (MissionSession.id == mission_id)
            )
            .limit(1)
        )

    def _find_by_session_id(self, db, session_id: str) -> Coupon | None:
        return db.scalar(
            select(Coupon).where(Coupon.mission_session_id == session_id).limit(1)
        )

    def _find_by_user_and_answer(self, db, user_id: str, answer: str) -> Coupon | None:
        return db.scalar(
            select(Coupon)
            .where(
                Coupon.user_id == user_id,
                Coupon.answer == answer,
                Coupon.status.in_(
                    [CouponStatus.ISSUED.value, CouponStatus.REDEEMED.value]
                ),
            )
            .limit(1)
        )

    def _new_unique_code(self, db, code_factory: Callable[[], str]) -> str:
        for _ in range(10):
            code = code_factory()
            if not db.scalar(select(Coupon.id).where(Coupon.code == code).limit(1)):
                return code
        raise RuntimeError("coupon_code_generation_failed")

    def _to_dict(self, db, model: Coupon) -> dict[str, Any]:
        mission_id = None
        if model.mission_session_id:
            session = db.get(MissionSession, model.mission_session_id)
            mission_id = (
                session.legacy_mission_id or session.id
                if session
                else model.mission_session_id
            )
        return {
            "code": model.code,
            "description": model.description,
            "mission_type": model.mission_type,
            "answer": model.answer,
            "mission_id": mission_id,
            "user_id": model.user_id,
            "partner_id": model.partner_id,
            "discount_rule": model.discount_rule,
            "status": model.status,
            "issued_at": _iso(model.issued_at),
            "expires_at": _iso(model.expires_at),
            "redeemed_at": _iso(model.redeemed_at),
            "partner_pos_id": model.partner_pos_id,
        }
