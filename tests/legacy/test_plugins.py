"""legacy 플러그인 단위 테스트.

검증 대상:
  - MissionPlugin (ABC): 직접 인스턴스화 불가
  - LocationMissionPlugin / PhotoMissionPlugin: mission_type, execute
  - MissionPluginRegistry: 싱글턴, register/get/list_types/ValueError
  - register_default_plugins: location·atmosphere 등록
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.legacy.plugins.base import MissionPlugin
from app.legacy.plugins.location_mission import LocationMissionPlugin
from app.legacy.plugins.photo_mission import PhotoMissionPlugin
from app.legacy.plugins.registry import MissionPluginRegistry, register_default_plugins


# ── 격리 픽스처 ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def fresh_plugin_registry():
    """각 테스트마다 MissionPluginRegistry 싱글턴을 초기화한다."""
    orig_instance = MissionPluginRegistry._instance
    orig_init = MissionPluginRegistry._initialized

    MissionPluginRegistry._instance = None
    MissionPluginRegistry._initialized = False

    yield

    MissionPluginRegistry._instance = orig_instance
    MissionPluginRegistry._initialized = orig_init


# ── MissionPlugin (ABC) ───────────────────────────────────────────────────────


class TestMissionPluginABC:
    def test_cannot_instantiate_abstract_class(self) -> None:
        with pytest.raises(TypeError):
            MissionPlugin()  # type: ignore[abstract]


# ── LocationMissionPlugin ─────────────────────────────────────────────────────


class TestLocationMissionPlugin:
    def test_mission_type_is_location(self) -> None:
        plugin = LocationMissionPlugin()
        assert plugin.mission_type == "location"

    def test_execute_delegates_to_run_mission1(self) -> None:
        plugin = LocationMissionPlugin()
        mock_result = {"success": True, "coupon": {"code": "ABCD1234"}}
        with patch(
            "app.legacy.mission_service.run_mission1", return_value=mock_result
        ) as m:
            result = plugin.execute("/img.jpg", "네모탑", {})
        m.assert_called_once_with("/img.jpg", "네모탑")
        assert result == mock_result

    def test_execute_returns_failure_dict(self) -> None:
        plugin = LocationMissionPlugin()
        mock_result = {"success": False, "hint": "Try again."}
        with patch("app.legacy.mission_service.run_mission1", return_value=mock_result):
            result = plugin.execute("/img.jpg", "피노키오", {})
        assert result["success"] is False


# ── PhotoMissionPlugin ────────────────────────────────────────────────────────


class TestPhotoMissionPlugin:
    def test_mission_type_is_atmosphere(self) -> None:
        plugin = PhotoMissionPlugin()
        assert plugin.mission_type == "atmosphere"

    def test_execute_delegates_to_run_mission2(self) -> None:
        plugin = PhotoMissionPlugin()
        mock_result = {"success": True, "coupon": {"code": "XY123456"}}
        with patch(
            "app.legacy.mission_service.run_mission2", return_value=mock_result
        ) as m:
            result = plugin.execute("/img.jpg", "차분한", {})
        m.assert_called_once_with("/img.jpg", "차분한")
        assert result == mock_result

    def test_execute_returns_failure_dict(self) -> None:
        plugin = PhotoMissionPlugin()
        mock_result = {"success": False, "hint": "More atmosphere needed."}
        with patch("app.legacy.mission_service.run_mission2", return_value=mock_result):
            result = plugin.execute("/img.jpg", "화사한", {})
        assert result["success"] is False


# ── MissionPluginRegistry ─────────────────────────────────────────────────────


class TestMissionPluginRegistry:
    def test_singleton(self) -> None:
        a = MissionPluginRegistry.get_instance()
        b = MissionPluginRegistry.get_instance()
        assert a is b

    def test_init_idempotent(self) -> None:
        reg = MissionPluginRegistry.get_instance()
        plugin = MagicMock(spec=MissionPlugin)
        plugin.mission_type = "test"
        reg.register(plugin)
        # 두 번째 init은 _plugins 초기화 안 함
        MissionPluginRegistry.__init__(reg)
        assert "test" in reg.list_types()

    def test_register_and_get(self) -> None:
        reg = MissionPluginRegistry.get_instance()
        plugin = MagicMock(spec=MissionPlugin)
        plugin.mission_type = "location"
        reg.register(plugin)
        assert reg.get("location") is plugin

    def test_get_unregistered_raises_value_error(self) -> None:
        reg = MissionPluginRegistry.get_instance()
        with pytest.raises(ValueError, match="not registered"):
            reg.get("unknown_type")

    def test_list_types_empty(self) -> None:
        reg = MissionPluginRegistry.get_instance()
        assert reg.list_types() == []

    def test_list_types_after_register(self) -> None:
        reg = MissionPluginRegistry.get_instance()
        p1 = MagicMock(spec=MissionPlugin)
        p1.mission_type = "location"
        p2 = MagicMock(spec=MissionPlugin)
        p2.mission_type = "atmosphere"
        reg.register(p1)
        reg.register(p2)
        types = reg.list_types()
        assert "location" in types
        assert "atmosphere" in types


# ── register_default_plugins ──────────────────────────────────────────────────


class TestRegisterDefaultPlugins:
    def test_registers_location_and_atmosphere(self) -> None:
        register_default_plugins()
        reg = MissionPluginRegistry.get_instance()
        types = reg.list_types()
        assert "location" in types
        assert "atmosphere" in types

    def test_location_plugin_type(self) -> None:
        register_default_plugins()
        reg = MissionPluginRegistry.get_instance()
        plugin = reg.get("location")
        assert plugin.mission_type == "location"

    def test_atmosphere_plugin_type(self) -> None:
        register_default_plugins()
        reg = MissionPluginRegistry.get_instance()
        plugin = reg.get("atmosphere")
        assert plugin.mission_type == "atmosphere"
