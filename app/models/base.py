"""VLM Probe 추상 기반 클래스 모듈."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class VLMProbe(ABC):
    """비전-언어 모델 프로브 인터페이스."""

    @abstractmethod
    def probe(
        self,
        mission_type: str,
        image_path: str,
        answer: str,
        prompt_bundle: dict[str, Any],
    ) -> dict[str, Any]:
        """이미지를 분석하여 모델 투표 결과를 반환한다.

        Args:
            mission_type: 미션 유형 ('location' | 'atmosphere').
            image_path: 분석할 이미지 파일 경로.
            answer: 미션 정답 키워드.
            prompt_bundle: 모델별 프롬프트 정보 딕셔너리.

        Returns:
            모델 투표 결과 딕셔너리 (model, score, label, reason).
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """모델 식별자를 반환한다.

        Returns:
            모델 이름 문자열.
        """
        ...
