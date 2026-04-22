"""pytest 전역 픽스처 및 환경 설정.

모든 테스트 실행 전에 이 파일이 자동으로 로드된다.

역할:
    - PAZULE_ENV=test 강제 주입:
        .env의 SKIP_METADATA_VALIDATION=true / BYPASS_MODEL_VALIDATION=true가
        pytest 실행에 스며들면 검증 로직이 건너뛰어져 mock이 무력화된다.
        이를 차단하기 위해 세션 시작 시 PAZULE_ENV=test를 환경변수에 주입하고,
        environments.py의 "test" 프로필(두 플래그 모두 False)이 적용되도록 한다.

    - settings 재초기화:
        load_dotenv()는 프로세스당 한 번만 실행되므로, conftest에서
        os.environ을 직접 조작한 뒤 Settings 인스턴스를 교체해
        테스트 전체에서 일관된 설정이 적용되도록 한다.

사용 예:
    # 개별 테스트에서 특정 설정만 바꾸고 싶을 때 (monkeypatch 사용)
    def test_something(monkeypatch):
        monkeypatch.setattr(settings, "LOCATION_PASS_THRESHOLD", 0.5)
        ...
"""

from __future__ import annotations

import os
import json

import pytest


def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    """pytest 세션 시작 시 가장 먼저 실행된다.

    .env 로드보다 먼저 PAZULE_ENV=test를 주입해,
    settings.py가 import될 때 test 프로필을 사용하도록 강제한다.

    Args:
        config: pytest Config 객체 (미사용, 시그니처 준수용).
    """
    os.environ.setdefault("PAZULE_ENV", "test")


@pytest.fixture(scope="session", autouse=True)
def _setup_test_data_dir(tmp_path_factory):
    """테스트 세션 전체에서 사용할 격리된 데이터 디렉터리 설정."""
    from app.core.config import settings
    import app.services.answer_service
    import app.services.mission_session_service
    import app.services.coupon_service

    # 1. 임시 디렉터리 생성
    test_data_dir = tmp_path_factory.mktemp("data")

    # 2. settings 오버라이드
    settings.DATA_DIR = str(test_data_dir)

    # 3. 이미 초기화된 서비스들의 경로 재설정
    if hasattr(app.services.mission_session_service, "mission_session_service"):
        svc = app.services.mission_session_service.mission_session_service
        svc._path = os.path.join(settings.DATA_DIR, "mission_sessions.json")

    if hasattr(app.services.answer_service, "ANSWER_FILE"):
        app.services.answer_service.ANSWER_FILE = os.path.join(
            settings.DATA_DIR, "answer.json"
        )
        # 테스트용 answer.json 기본 파일 생성 (필요 시)
        with open(app.services.answer_service.ANSWER_FILE, "w", encoding="utf-8") as f:
            json.dump({"mission-location": [], "mission-atmosphere": []}, f)

    if hasattr(app.services.answer_service, "STATE_FILE"):
        app.services.answer_service.STATE_FILE = os.path.join(
            settings.DATA_DIR, "current_answer.json"
        )

    yield test_data_dir


@pytest.fixture(autouse=True)
def _force_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """모든 테스트에 자동 적용되는 환경 격리 픽스처.

    개발 편의를 위한 dev 플래그(SKIP_METADATA_VALIDATION, BYPASS_MODEL_VALIDATION)가
    .env에 설정되어 있더라도 테스트 실행 중에는 반드시 False로 유지된다.

    이중 방어:
        1. pytest_configure: 세션 시작 시 PAZULE_ENV=test 주입 (import 시점 보호)
        2. 이 픽스처: 개별 테스트 실행 시 os.environ 직접 오버라이드 (런타임 보호)

    Args:
        monkeypatch: pytest 내장 monkeypatch 픽스처. 테스트 종료 후 자동 복원.
    """
    monkeypatch.setenv("PAZULE_ENV", "test")
    monkeypatch.setenv("SKIP_METADATA_VALIDATION", "false")
    monkeypatch.setenv("BYPASS_MODEL_VALIDATION", "false")
