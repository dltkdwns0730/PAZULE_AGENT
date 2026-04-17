"""위치 미션 플러그인: mission_service.run_mission1 래퍼."""

from __future__ import annotations

import logging
from typing import Any

from app.plugins.base import MissionPlugin

logger = logging.getLogger(__name__)


class LocationMissionPlugin(MissionPlugin):
    """장소 찾기 미션 플러그인."""

    @property
    def mission_type(self) -> str:
        """미션 유형 식별자를 반환한다.

        Returns:
            'location'.
        """
        return "location"

    def execute(
        self, image_path: str, answer: str, prompt_bundle: dict[str, Any]
    ) -> dict[str, Any]:
        """장소 찾기 미션을 실행한다.

        Args:
            image_path: 분석할 이미지 파일 경로.
            answer: 미션 정답 키워드.
            prompt_bundle: 모델별 프롬프트 정보 딕셔너리.

        Returns:
            미션 실행 결과 딕셔너리.
        """
        from app.services.mission_service import run_mission1

        return run_mission1(image_path, answer)
