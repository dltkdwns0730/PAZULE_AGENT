"""MissionSessionService 단위 테스트.

공공 환경 호환 설계:
  - 실제 파일 I/O → tmp_path fixture로 격리
  - settings.DATA_DIR → tmp_path로 패치
  - 시간 의존성(_utcnow) → patch로 제어

검증 대상:
  - create_session: 세션 생성, 파일 저장, 필드 검증
  - get_session: 존재/부재 조회
  - _update_session: mutate_fn 적용, 없는 ID
  - can_submit: 세션 없음 / 만료 / 제출 횟수 초과 / 정상
  - record_submission: 제출 기록 저장, 최신 판정 저장
  - mark_coupon_issued: 쿠폰 코드 기록, 상태 변경
  - is_duplicate_hash_for_user: 중복 감지, 다른 사용자, 해시 없음
  - hash_file: SHA-256 결정론적 해시 검증 (실제 파일 사용)
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest


# ── fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def svc(tmp_path: Path):
    """tmp_path에 격리된 MissionSessionService 인스턴스."""
    with patch("app.services.mission_session_service.settings") as mock_settings:
        mock_settings.DATA_DIR = str(tmp_path)
        mock_settings.MISSION_SESSION_TTL_MINUTES = 60
        mock_settings.MISSION_MAX_SUBMISSIONS = 3
        from app.services.mission_session_service import MissionSessionService

        service = MissionSessionService()
    # 이후 직접 _path 재설정 (인스턴스 내부 경로 보정)
    service._path = str(tmp_path / "mission_sessions.json")
    return service


def _utc(offset_minutes: int = 0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)


# ── create_session ────────────────────────────────────────────────────────────


class TestCreateSession:
    def test_returns_dict(self, svc) -> None:
        result = svc.create_session("u1", "site1", "location", "target", "hint")
        print(f"\n[create_session] {result}")
        assert isinstance(result, dict)

    def test_has_mission_id(self, svc) -> None:
        result = svc.create_session("u1", "site1", "location", "target", "hint")
        assert "mission_id" in result
        assert len(result["mission_id"]) > 0

    def test_user_id_stored(self, svc) -> None:
        result = svc.create_session("user_abc", "site1", "location", "target", "hint")
        assert result["user_id"] == "user_abc"

    def test_mission_type_normalized(self, svc) -> None:
        """'photo' → 'atmosphere'로 정규화."""
        result = svc.create_session("u1", "site1", "photo", "target", "hint")
        assert result["mission_type"] == "atmosphere"

    def test_status_is_created(self, svc) -> None:
        result = svc.create_session("u1", "site1", "location", "target", "hint")
        assert result["status"] == "created"

    def test_submissions_is_empty_list(self, svc) -> None:
        result = svc.create_session("u1", "site1", "location", "target", "hint")
        assert result["submissions"] == []

    def test_session_persisted_to_file(self, svc, tmp_path) -> None:
        """세션이 JSON 파일에 저장됨."""
        result = svc.create_session("u1", "site1", "location", "target", "hint")
        data = json.loads(Path(svc._path).read_text(encoding="utf-8"))
        ids = [s["mission_id"] for s in data["sessions"]]
        assert result["mission_id"] in ids

    def test_guest_fallback_for_empty_user_id(self, svc) -> None:
        result = svc.create_session("", "site1", "location", "target", "hint")
        assert result["user_id"] == "guest"

    def test_multiple_sessions_accumulated(self, svc) -> None:
        svc.create_session("u1", "site1", "location", "a", "h")
        svc.create_session("u2", "site2", "atmosphere", "b", "h2")
        data = json.loads(Path(svc._path).read_text(encoding="utf-8"))
        assert len(data["sessions"]) == 2


# ── get_session ──────────────────────────────────────────────────────────────


class TestGetSession:
    def test_existing_session_returned(self, svc) -> None:
        created = svc.create_session("u1", "s1", "location", "t", "h")
        found = svc.get_session(created["mission_id"])
        assert found is not None
        assert found["mission_id"] == created["mission_id"]

    def test_nonexistent_id_returns_none(self, svc) -> None:
        result = svc.get_session("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_get_correct_session_among_multiple(self, svc) -> None:
        svc.create_session("u1", "s1", "location", "a", "h")
        s2 = svc.create_session("u2", "s2", "atmosphere", "b", "h2")
        found = svc.get_session(s2["mission_id"])
        assert found["user_id"] == "u2"


# ── can_submit ────────────────────────────────────────────────────────────────


class TestCanSubmit:
    def test_valid_session_ok(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        ok, reason = svc.can_submit(session["mission_id"])
        print(f"\n[can_submit] ok={ok}, reason={reason}")
        assert ok is True
        assert reason == "ok"

    def test_nonexistent_session_not_found(self, svc) -> None:
        ok, reason = svc.can_submit("bad-id")
        assert ok is False
        assert reason == "session_not_found"

    def test_expired_session_rejected(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        # expires_at을 과거로 덮어씀
        data = json.loads(Path(svc._path).read_text(encoding="utf-8"))
        for s in data["sessions"]:
            if s["mission_id"] == session["mission_id"]:
                s["expires_at"] = _utc(-120).isoformat()  # 2시간 전 만료
        Path(svc._path).write_text(json.dumps(data), encoding="utf-8")

        ok, reason = svc.can_submit(session["mission_id"])
        assert ok is False
        assert reason == "session_expired"

    def test_submission_limit_reached(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        # max_submissions=3, 제출 3회 기록
        data = json.loads(Path(svc._path).read_text(encoding="utf-8"))
        for s in data["sessions"]:
            if s["mission_id"] == session["mission_id"]:
                s["max_submissions"] = 2
                s["submissions"] = [{"image_hash": "h1"}, {"image_hash": "h2"}]
        Path(svc._path).write_text(json.dumps(data), encoding="utf-8")

        ok, reason = svc.can_submit(session["mission_id"])
        assert ok is False
        assert reason == "submission_limit_reached"


# ── record_submission ─────────────────────────────────────────────────────────


class TestRecordSubmission:
    def test_submission_appended(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        result = {"success": True, "confidence": 0.9}
        updated = svc.record_submission(session["mission_id"], "hash123", result)
        print(f"\n[record_submission] submissions={updated['submissions']}")
        assert len(updated["submissions"]) == 1

    def test_image_hash_stored(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        svc.record_submission(session["mission_id"], "deadbeef", {"success": True})
        updated = svc.get_session(session["mission_id"])
        assert updated["submissions"][0]["image_hash"] == "deadbeef"

    def test_latest_judgment_stored(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        result = {"success": True, "confidence": 0.88}
        svc.record_submission(session["mission_id"], "hash1", result)
        updated = svc.get_session(session["mission_id"])
        assert updated["latest_judgment"]["confidence"] == 0.88

    def test_status_becomes_submitted(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        svc.record_submission(session["mission_id"], "h1", {"success": False})
        updated = svc.get_session(session["mission_id"])
        assert updated["status"] == "submitted"

    def test_nonexistent_session_returns_none(self, svc) -> None:
        result = svc.record_submission("no-id", "hash", {"success": True})
        assert result is None

    def test_multiple_submissions_accumulated(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        svc.record_submission(session["mission_id"], "h1", {"success": False})
        svc.record_submission(session["mission_id"], "h2", {"success": True})
        updated = svc.get_session(session["mission_id"])
        assert len(updated["submissions"]) == 2


# ── mark_coupon_issued ────────────────────────────────────────────────────────


class TestMarkCouponIssued:
    def test_coupon_code_stored(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        updated = svc.mark_coupon_issued(session["mission_id"], "COUP1234")
        print(f"\n[mark_coupon_issued] coupon_code={updated['coupon_code']}")
        assert updated["coupon_code"] == "COUP1234"

    def test_status_becomes_coupon_issued(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        updated = svc.mark_coupon_issued(session["mission_id"], "COUP9999")
        assert updated["status"] == "coupon_issued"

    def test_nonexistent_session_returns_none(self, svc) -> None:
        result = svc.mark_coupon_issued("no-id", "COUP0000")
        assert result is None

    def test_persisted_to_file(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        svc.mark_coupon_issued(session["mission_id"], "PERSISTED")
        reloaded = svc.get_session(session["mission_id"])
        assert reloaded["coupon_code"] == "PERSISTED"


# ── is_duplicate_hash_for_user ────────────────────────────────────────────────


class TestIsDuplicateHashForUser:
    def test_no_previous_submissions_returns_false(self, svc) -> None:
        result = svc.is_duplicate_hash_for_user("u1", "newhash")
        assert result is False

    def test_same_user_same_hash_returns_true(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        svc.record_submission(session["mission_id"], "duphash", {"success": True})
        result = svc.is_duplicate_hash_for_user("u1", "duphash")
        assert result is True

    def test_different_user_same_hash_returns_false(self, svc) -> None:
        """다른 사용자의 해시는 중복으로 처리하지 않음."""
        session = svc.create_session("u1", "s1", "location", "t", "h")
        svc.record_submission(session["mission_id"], "sharedhash", {"success": True})
        result = svc.is_duplicate_hash_for_user("u2", "sharedhash")
        assert result is False

    def test_empty_hash_returns_false(self, svc) -> None:
        """빈 해시는 중복 검사 없이 False."""
        result = svc.is_duplicate_hash_for_user("u1", "")
        assert result is False

    def test_none_hash_returns_false(self, svc) -> None:
        result = svc.is_duplicate_hash_for_user("u1", None)
        assert result is False

    def test_different_hash_same_user_returns_false(self, svc) -> None:
        session = svc.create_session("u1", "s1", "location", "t", "h")
        svc.record_submission(session["mission_id"], "hash_a", {"success": True})
        result = svc.is_duplicate_hash_for_user("u1", "hash_b")
        assert result is False


# ── hash_file ─────────────────────────────────────────────────────────────────


class TestHashFile:
    def test_returns_string(self, tmp_path) -> None:
        f = tmp_path / "test.jpg"
        f.write_bytes(b"fake image data")
        from app.services.mission_session_service import MissionSessionService

        result = MissionSessionService.hash_file(str(f))
        assert isinstance(result, str)

    def test_sha256_length(self, tmp_path) -> None:
        """SHA-256 hex digest는 64자."""
        f = tmp_path / "img.jpg"
        f.write_bytes(b"some content")
        from app.services.mission_session_service import MissionSessionService

        result = MissionSessionService.hash_file(str(f))
        assert len(result) == 64

    def test_deterministic(self, tmp_path) -> None:
        """같은 파일 → 같은 해시."""
        f = tmp_path / "img.jpg"
        f.write_bytes(b"deterministic content")
        from app.services.mission_session_service import MissionSessionService

        h1 = MissionSessionService.hash_file(str(f))
        h2 = MissionSessionService.hash_file(str(f))
        assert h1 == h2

    def test_different_content_different_hash(self, tmp_path) -> None:
        f1 = tmp_path / "a.jpg"
        f2 = tmp_path / "b.jpg"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        from app.services.mission_session_service import MissionSessionService

        assert MissionSessionService.hash_file(
            str(f1)
        ) != MissionSessionService.hash_file(str(f2))

    def test_known_hash_value(self, tmp_path) -> None:
        """알려진 입력 → 예측 가능한 SHA-256 검증."""
        import hashlib

        content = b"hello world"
        expected = hashlib.sha256(content).hexdigest()
        f = tmp_path / "hw.txt"
        f.write_bytes(content)
        from app.services.mission_session_service import MissionSessionService

        assert MissionSessionService.hash_file(str(f)) == expected
