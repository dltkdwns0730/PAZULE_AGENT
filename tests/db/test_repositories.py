from __future__ import annotations

from sqlalchemy import create_engine

from app.db.models import Base
from app.db.repositories import CouponRepository, MissionSessionRepository
from app.services.coupon_service import CouponService
from app.services.mission_session_service import MissionSessionService


def _database_url(tmp_path) -> str:
    path = tmp_path / "pazule-repositories.db"
    url = f"sqlite:///{path}"
    engine = create_engine(url, future=True)
    Base.metadata.create_all(engine)
    engine.dispose()
    return url


def test_mission_session_repository_records_submission_and_duplicate_hash(tmp_path):
    repo = MissionSessionRepository(_database_url(tmp_path))
    session = repo.create_session(
        user_id="user-1",
        site_id="site-1",
        mission_type="location",
        answer="answer",
        hint="hint",
    )

    can_submit, reason = repo.can_submit(session["mission_id"])
    assert can_submit is True
    assert reason == "ok"

    updated = repo.record_submission(
        session["mission_id"],
        "hash-1",
        {"success": True, "confidence": 0.91},
    )

    assert updated["status"] == "submitted"
    assert updated["latest_judgment"]["success"] is True
    assert updated["submissions"][0]["image_hash"] == "hash-1"
    assert repo.is_duplicate_hash_for_user("user-1", "hash-1") is True
    assert repo.is_mission_completed_today("user-1", "location") is True


def test_coupon_repository_is_idempotent_and_redeems_once(tmp_path):
    url = _database_url(tmp_path)
    sessions = MissionSessionRepository(url)
    coupons = CouponRepository(url)
    session = sessions.create_session(
        user_id="user-2",
        site_id="site-2",
        mission_type="atmosphere",
        answer="answer-2",
        hint="hint",
    )
    sessions.record_submission(session["mission_id"], "hash-2", {"success": True})

    codes = iter(["CODE0001", "CODE0002"])
    first = coupons.issue_coupon(
        mission_type="mission2",
        answer="answer-2",
        mission_id=session["mission_id"],
        user_id="user-2",
        code_factory=lambda: next(codes),
    )
    second = coupons.issue_coupon(
        mission_type="mission2",
        answer="answer-2",
        mission_id=session["mission_id"],
        user_id="user-2",
        code_factory=lambda: next(codes),
    )

    assert first["code"] == "CODE0001"
    assert second["code"] == first["code"]
    assert second["mission_id"] == session["mission_id"]
    assert coupons.has_coupon_for_answer("user-2", "answer-2") is True
    assert coupons.get_user_coupons("user-2")[0]["code"] == first["code"]

    redeemed = coupons.redeem_coupon(first["code"], "POS-1")
    duplicate = coupons.redeem_coupon(first["code"], "POS-1")

    assert redeemed["redeem_status"] == "redeemed"
    assert duplicate["redeem_status"] == "already_redeemed"


def test_services_can_use_db_storage_backend(tmp_path, monkeypatch):
    url = _database_url(tmp_path)
    monkeypatch.setattr("app.core.config.settings.STORAGE_BACKEND", "db")

    sessions = MissionSessionService()
    sessions._db_repository = MissionSessionRepository(url)
    coupons = CouponService()
    coupons._db_repository = CouponRepository(url)

    session = sessions.create_session(
        user_id="user-3",
        site_id="site-3",
        mission_type="location",
        answer="answer-3",
        hint="hint",
    )
    sessions.record_submission(session["mission_id"], "hash-3", {"success": True})
    coupon = coupons.issue_coupon(
        mission_type="mission1",
        answer="answer-3",
        mission_id=session["mission_id"],
        user_id="user-3",
    )
    sessions.mark_coupon_issued(session["mission_id"], coupon["code"])

    assert sessions.get_session(session["mission_id"])["status"] == "coupon_issued"
    assert coupons.get_user_coupons("user-3")[0]["code"] == coupon["code"]
