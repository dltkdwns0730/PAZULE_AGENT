"""VLM Probe abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class VLMProbe(ABC):
    """비전-언어 모델 프로브 인터페이스."""

    @abstractmethod
    def probe(
        self,
        mission_type: str,
        image_path: str,
        answer: str,
        prompt_bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        """이미지를 분석하여 모델 투표 결과를 반환한다."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...
