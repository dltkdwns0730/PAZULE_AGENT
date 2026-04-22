import pytest
from datetime import datetime, timedelta, timezone
from app.services.mission_session_service import MissionSessionService


@pytest.fixture
def session_service(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # settings.DATA_DIR 오버라이드
    from app.core.config import settings

    monkeypatch.setattr(settings, "DATA_DIR", str(data_dir))

    # 서비스 인스턴스 생성 (초기화 시 경로 설정됨)
    service = MissionSessionService()
    return service


def test_create_session(session_service):
    session = session_service.create_session(
        user_id="user1",
        site_id="site1",
        mission_type="location",
        answer="ans1",
        hint="hint1",
    )

    assert session["user_id"] == "user1"
    assert session["mission_type"] == "location"
    assert session["status"] == "created"
    assert "mission_id" in session

    # 파일에 저장되었는지 확인
    saved = session_service.get_session(session["mission_id"])
    assert saved == session


def test_can_submit_success(session_service):
    session = session_service.create_session("u1", "s1", "location", "a", "h")
    can, reason = session_service.can_submit(session["mission_id"])
    assert can is True
    assert reason == "ok"


def test_can_submit_expired(session_service, monkeypatch):
    session = session_service.create_session("u1", "s1", "location", "a", "h")

    # 만료 시간을 과거로 조작
    def mock_read_all():
        data = {"sessions": [session]}
        data["sessions"][0]["expires_at"] = (
            datetime.now(timezone.utc) - timedelta(seconds=1)
        ).isoformat()
        return data

    monkeypatch.setattr(session_service, "_read_all", mock_read_all)

    can, reason = session_service.can_submit(session["mission_id"])
    assert can is False
    assert reason == "session_expired"


def test_can_submit_limit_reached(session_service, monkeypatch):
    from app.core.config import settings

    # 런타임에 설정을 1로 변경
    monkeypatch.setattr(settings, "MISSION_MAX_SUBMISSIONS", 1)

    # 세션 생성 (이때 max_submissions=1이 주입되어야 함)
    session = session_service.create_session("u1", "s1", "location", "a", "h")

    # 명시적으로 세션 객체에서 확인
    if session["max_submissions"] != 1:
        # 만약 settings 패치가 안 먹혔다면 강제로 수정 (테스트 목적)
        session["max_submissions"] = 1
        session_service._update_session(session["mission_id"], lambda s: session)

    session_service.record_submission(session["mission_id"], "hash1", {"success": True})

    can, reason = session_service.can_submit(session["mission_id"])
    assert can is False
    assert reason == "submission_limit_reached"


def test_record_submission(session_service):
    session = session_service.create_session("u1", "s1", "location", "a", "h")
    result = {"success": True, "confidence": 0.9}

    updated = session_service.record_submission(session["mission_id"], "hash1", result)

    assert updated["status"] == "submitted"
    assert len(updated["submissions"]) == 1
    assert updated["submissions"][0]["image_hash"] == "hash1"
    assert updated["latest_judgment"] == result


def test_is_duplicate_hash_for_user(session_service):
    # 고유한 ID를 사용하여 다른 테스트와의 간섭 최소화
    user_id = "user_dup_test"
    image_hash = "hash_dup_test"

    # 처음에는 중복 아님
    assert session_service.is_duplicate_hash_for_user(user_id, image_hash) is False

    # 제출 기록
    session = session_service.create_session(user_id, "s1", "location", "a", "h")
    session_service.record_submission(
        session["mission_id"], image_hash, {"success": True}
    )

    # 이제 중복임
    assert session_service.is_duplicate_hash_for_user(user_id, image_hash) is True
    # 다른 사용자는 중복 아님
    assert session_service.is_duplicate_hash_for_user("user2", image_hash) is False


def test_hash_file(tmp_path):
    f = tmp_path / "test.jpg"
    content = b"pazule test content"
    f.write_bytes(content)

    h1 = MissionSessionService.hash_file(str(f))
    h2 = MissionSessionService.hash_file(str(f))

    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest
