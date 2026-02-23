"""Mission plugin registry."""

from __future__ import annotations

from typing import Dict, Optional

from app.plugins.base import MissionPlugin


class MissionPluginRegistry:
    """싱글턴 미션 플러그인 레지스트리."""

    _instance: Optional[MissionPluginRegistry] = None
    _initialized: bool = False

    def __new__(cls) -> MissionPluginRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._plugins: Dict[str, MissionPlugin] = {}
        self._initialized = True

    @classmethod
    def get_instance(cls) -> MissionPluginRegistry:
        return cls()

    def register(self, plugin: MissionPlugin) -> None:
        self._plugins[plugin.mission_type] = plugin

    def get(self, mission_type: str) -> MissionPlugin:
        if mission_type not in self._plugins:
            raise ValueError(
                f"Mission plugin '{mission_type}' not registered. "
                f"Available: {list(self._plugins.keys())}"
            )
        return self._plugins[mission_type]

    def list_types(self) -> list[str]:
        return list(self._plugins.keys())


def register_default_plugins() -> None:
    """기본 미션 플러그인을 레지스트리에 등록한다."""
    from app.plugins.location_mission import LocationMissionPlugin
    from app.plugins.photo_mission import PhotoMissionPlugin

    registry = MissionPluginRegistry.get_instance()
    registry.register(LocationMissionPlugin())
    registry.register(PhotoMissionPlugin())
