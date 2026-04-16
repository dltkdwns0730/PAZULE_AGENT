"""Phase 1 리팩터 검증: config 패키지 import 경로 하위 호환성 테스트.

리팩터 목적: config.py → config/ 패키지 전환 후에도
  'from app.core.config import settings' 경로가 깨지지 않아야 한다.
검증 기준:
  - 기존 import 경로 11곳 모두 호환
  - constants 모듈이 새로운 경로로 접근 가능
  - settings 내 주요 필드가 정상 로드됨
"""

from __future__ import annotations

import types


class TestBackwardCompatibleImport:
    """'from app.core.config import settings' 하위 호환 검증."""

    def test_settings_importable_from_config(self) -> None:
        """기존 import 경로가 유효해야 한다."""
        from app.core.config import settings  # noqa: F401 (import check)

        assert settings is not None

    def test_settings_is_not_module(self) -> None:
        """settings는 모듈이 아닌 Settings 인스턴스여야 한다."""
        from app.core.config import settings

        assert not isinstance(settings, types.ModuleType)

    def test_settings_has_base_dir(self) -> None:
        from app.core.config import settings

        assert hasattr(settings, "BASE_DIR")

    def test_settings_has_data_dir(self) -> None:
        from app.core.config import settings

        assert hasattr(settings, "DATA_DIR")

    def test_settings_has_blip_model_id(self) -> None:
        from app.core.config import settings

        assert hasattr(settings, "BLIP_MODEL_ID")

    def test_settings_has_skip_metadata_validation(self) -> None:
        from app.core.config import settings

        assert hasattr(settings, "SKIP_METADATA_VALIDATION")
        assert isinstance(settings.SKIP_METADATA_VALIDATION, bool)

    def test_settings_has_bypass_model_validation(self) -> None:
        from app.core.config import settings

        assert hasattr(settings, "BYPASS_MODEL_VALIDATION")
        assert isinstance(settings.BYPASS_MODEL_VALIDATION, bool)

    def test_settings_has_mission_session_ttl(self) -> None:
        from app.core.config import settings

        assert hasattr(settings, "MISSION_SESSION_TTL_MINUTES")
        assert isinstance(settings.MISSION_SESSION_TTL_MINUTES, int)

    def test_settings_has_api_timeout_seconds(self) -> None:
        from app.core.config import settings

        assert hasattr(settings, "API_TIMEOUT_SECONDS")
        assert isinstance(settings.API_TIMEOUT_SECONDS, (int, float))

    def test_settings_base_dir_is_str(self) -> None:
        from app.core.config import settings

        assert isinstance(settings.BASE_DIR, str)

    def test_settings_base_dir_points_to_project_root(self) -> None:
        """BASE_DIR이 프로젝트 루트(pyproject.toml 위치)를 가리켜야 한다."""
        import os

        from app.core.config import settings

        pyproject = os.path.join(settings.BASE_DIR, "pyproject.toml")
        assert os.path.exists(pyproject), (
            f"BASE_DIR={settings.BASE_DIR!r}에 pyproject.toml이 없음 — "
            "settings.py 이동 후 경로 깊이가 잘못 계산되었을 수 있음"
        )


class TestConstantsModuleImport:
    """constants 모듈 import 경로 검증."""

    def test_constants_importable_from_config(self) -> None:
        from app.core.config import constants  # noqa: F401

        assert constants is not None

    def test_constants_is_module(self) -> None:
        from app.core.config import constants

        assert isinstance(constants, types.ModuleType)

    def test_constants_direct_import(self) -> None:
        """constants 모듈을 직접 경로로도 import 가능해야 한다."""
        import importlib

        mod = importlib.import_module("app.core.config.constants")
        assert mod is not None

    def test_constants_direct_attribute_import(self) -> None:
        """constants 내 특정 상수를 직접 import 가능해야 한다."""
        from app.core.config.constants import ALLOWED_UPLOAD_EXTENSIONS

        assert ALLOWED_UPLOAD_EXTENSIONS is not None

    def test_all_exports(self) -> None:
        """config 패키지 __all__이 settings·constants를 포함해야 한다."""
        import app.core.config as config_pkg

        assert "settings" in config_pkg.__all__
        assert "constants" in config_pkg.__all__


class TestSettingsModuleImport:
    """settings.py 단독 import 경로 검증."""

    def test_settings_importable_from_settings_module(self) -> None:
        from app.core.config.settings import settings  # noqa: F401

        assert settings is not None

    def test_both_paths_return_same_object(self) -> None:
        """패키지 경로와 모듈 직접 경로가 동일 객체를 반환해야 한다."""
        from app.core.config import settings as s1
        from app.core.config.settings import settings as s2

        assert s1 is s2
