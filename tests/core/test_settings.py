import importlib
import sys
from app.core.config.environments import get_profile, PROFILES


class TestEnvironmentProfile:
    """environments.py get_profile() 동작 검증."""

    def test_unknown_env_falls_back_to_production(self):
        """알 수 없는 환경 이름은 production 프로필로 폴백한다."""
        profile = get_profile("nonexistent")
        assert profile == PROFILES["production"]
        assert profile["SKIP_METADATA_VALIDATION"] is False
        assert profile["BYPASS_MODEL_VALIDATION"] is False

    def test_development_enables_both_bypass_flags(self):
        """development 프로필은 두 bypass 플래그를 True로 설정한다."""
        profile = get_profile("development")
        assert profile["SKIP_METADATA_VALIDATION"] is True
        assert profile["BYPASS_MODEL_VALIDATION"] is True
        assert profile["SKIP_GPS_VALIDATION"] is True

    def test_test_profile_disables_all_bypass_flags(self):
        """test 프로필은 두 bypass 플래그를 False로 설정한다 (mock 활성화)."""
        profile = get_profile("test")
        assert profile["SKIP_METADATA_VALIDATION"] is False
        assert profile["BYPASS_MODEL_VALIDATION"] is False
        assert profile["SKIP_GPS_VALIDATION"] is False


class TestSettingsEnvPriority:
    """settings._env_or_profile(): .env > profile 우선순위 검증."""

    def reload_settings(self):
        """settings 모듈과 상위 패키지에서 캐시된 인스턴스를 제거하고 다시 로드한다."""
        # 1. 관련 모듈 캐시 삭제
        modules_to_reload = ["app.core.config.settings", "app.core.config"]
        for mod_name in modules_to_reload:
            if mod_name in sys.modules:
                del sys.modules[mod_name]

        # 2. 다시 import하여 새 인스턴스 생성 유도
        importlib.import_module("app.core.config.settings")
        config_mod = importlib.import_module("app.core.config")
        return config_mod.settings

    def test_env_var_overrides_profile(self, monkeypatch):
        """os.environ이 설정되면 profile 값보다 우선한다."""
        monkeypatch.setenv("LOCATION_PASS_THRESHOLD", "0.99")
        monkeypatch.setenv("PAZULE_ENV", "production")

        settings = self.reload_settings()

        assert settings.LOCATION_PASS_THRESHOLD == 0.99
        assert settings.ENV == "production"

    def test_missing_env_uses_profile_value(self, monkeypatch):
        """os.environ이 없으면 profile 기본값을 사용한다."""
        monkeypatch.delenv("LOCATION_PASS_THRESHOLD", raising=False)
        monkeypatch.setenv("PAZULE_ENV", "production")

        settings = self.reload_settings()

        # production 프로필의 기본값은 0.70
        assert settings.LOCATION_PASS_THRESHOLD == 0.70

    def test_test_env_forces_skip_metadata_false(self, monkeypatch):
        """PAZULE_ENV=test일 때 SKIP_METADATA_VALIDATION은 반드시 False."""
        monkeypatch.setenv("PAZULE_ENV", "test")

        settings = self.reload_settings()

        assert settings.ENV == "test"
        assert settings.SKIP_METADATA_VALIDATION is False

    def test_test_env_forces_bypass_model_false(self, monkeypatch):
        """PAZULE_ENV=test일 때 BYPASS_MODEL_VALIDATION은 반드시 False."""
        monkeypatch.setenv("PAZULE_ENV", "test")

        settings = self.reload_settings()

        assert settings.BYPASS_MODEL_VALIDATION is False
