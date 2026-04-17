"""미션 플러그인 레지스트리."""

from __future__ import annotations

import logging

from app.plugins.base import MissionPlugin

logger = logging.getLogger(__name__)


class MissionPluginRegistry:
    """싱글턴 미션 플러그인 레지스트리."""

    _instance: MissionPluginRegistry | None = None
    _initialized: bool = False

    def __new__(cls) -> MissionPluginRegistry:
        """싱글턴 인스턴스를 반환한다."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """레지스트리를 초기화한다 (최초 1회만 실행)."""
        if self._initialized:
            return
        self._plugins: dict[str, MissionPlugin] = {}
        self._initialized = True

    @classmethod
    def get_instance(cls) -> MissionPluginRegistry:
        """싱글턴 인스턴스를 반환한다.

        Returns:
            MissionPluginRegistry 싱글턴 인스턴스.
        """
        return cls()

    def register(self, plugin: MissionPlugin) -> None:
        """미션 플러그인을 레지스트리에 등록한다.

        Args:
            plugin: 등록할 MissionPlugin 인스턴스.
        """
        self._plugins[plugin.mission_type] = plugin

    def get(self, mission_type: str) -> MissionPlugin:
        """미션 유형으로 플러그인을 조회한다.

        Args:
            mission_type: 미션 유형 식별자.

        Returns:
            등록된 MissionPlugin 인스턴스.

        Raises:
            ValueError: 해당 미션 유형의 플러그인이 등록되지 않은 경우.
        """
        if mission_type not in self._plugins:
            raise ValueError(
                f"Mission plugin '{mission_type}' not registered. "
                f"Available: {list(self._plugins.keys())}"
            )
        return self._plugins[mission_type]

    def list_types(self) -> list[str]:
        """등록된 미션 유형 목록을 반환한다.

        Returns:
            미션 유형 문자열 목록.
        """
        return list(self._plugins.keys())


def register_default_plugins() -> None:
    """기본 미션 플러그인을 레지스트리에 등록한다."""
    from app.plugins.location_mission import LocationMissionPlugin
    from app.plugins.photo_mission import PhotoMissionPlugin

    registry = MissionPluginRegistry.get_instance()
    registry.register(LocationMissionPlugin())
    registry.register(PhotoMissionPlugin())
