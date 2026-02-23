"""Photo (atmosphere) mission plugin: wraps mission_service.run_mission2."""

from __future__ import annotations

from typing import Any, Dict

from app.plugins.base import MissionPlugin


class PhotoMissionPlugin(MissionPlugin):
    @property
    def mission_type(self) -> str:
        return "atmosphere"

    def execute(
        self, image_path: str, answer: str, prompt_bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        from app.services.mission_service import run_mission2

        return run_mission2(image_path, answer)
