"""미션 플러그인 추상 기반 클래스 모듈."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class MissionPlugin(ABC):
    """미션 플러그인 추상 인터페이스."""

    @property
    @abstractmethod
    def mission_type(self) -> str:
        """플러그인이 처리하는 미션 유형 식별자를 반환한다.

        Returns:
            미션 유형 문자열 ('location' | 'atmosphere').
        """
        ...

    @abstractmethod
    def execute(
        self, image_path: str, answer: str, prompt_bundle: dict[str, Any]
    ) -> dict[str, Any]:
        """미션을 실행하고 결과를 반환한다.

        Args:
            image_path: 분석할 이미지 파일 경로.
            answer: 미션 정답 키워드.
            prompt_bundle: 모델별 프롬프트 정보 딕셔너리.

        Returns:
            미션 실행 결과 딕셔너리.
        """
        ...
