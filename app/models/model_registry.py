"""모델 레지스트리: VLMProbe 등록 및 조회."""

from __future__ import annotations

import logging
from typing import Any

from app.models.base import VLMProbe

logger = logging.getLogger(__name__)


class _BLIPProbe(VLMProbe):
    """BLIP VQA 모델 프로브."""

    @property
    def model_name(self) -> str:
        """모델 식별자를 반환한다."""
        return "blip"

    def probe(
        self,
        mission_type: str,
        image_path: str,
        answer: str,
        prompt_bundle: dict[str, Any],
    ) -> dict[str, Any]:
        """미션 유형에 따라 BLIP location 또는 atmosphere 프로브를 실행한다.

        Args:
            mission_type: 미션 유형 ('location' | 'atmosphere').
            image_path: 이미지 파일 경로.
            answer: 미션 정답 키워드.
            prompt_bundle: 모델별 프롬프트 정보.

        Returns:
            모델 투표 결과 딕셔너리.
        """
        from app.models.blip import probe_with_blip_atmosphere, probe_with_blip_location

        if mission_type == "location":
            return probe_with_blip_location(image_path, answer, prompt_bundle)
        return probe_with_blip_atmosphere(image_path, answer, prompt_bundle)


class _QwenProbe(VLMProbe):
    """Qwen-VL 모델 프로브 (OpenRouter 경유)."""

    @property
    def model_name(self) -> str:
        """모델 식별자를 반환한다."""
        return "qwen"

    def probe(
        self,
        mission_type: str,
        image_path: str,
        answer: str,
        prompt_bundle: dict[str, Any],
    ) -> dict[str, Any]:
        """OpenRouter를 통해 Qwen-VL 프로브를 실행한다.

        Args:
            mission_type: 미션 유형.
            image_path: 이미지 파일 경로.
            answer: 미션 정답 키워드.
            prompt_bundle: 모델별 프롬프트 정보.

        Returns:
            모델 투표 결과 딕셔너리.
        """
        from app.models.qwen_vl import probe_with_qwen

        return probe_with_qwen(mission_type, image_path, answer, prompt_bundle)


class _SigLIP2Probe(VLMProbe):
    """SigLIP2 모델 프로브 (HuggingFace)."""

    @property
    def model_name(self) -> str:
        """모델 식별자를 반환한다."""
        return "siglip2"

    def probe(
        self,
        mission_type: str,
        image_path: str,
        answer: str,
        prompt_bundle: dict[str, Any],
    ) -> dict[str, Any]:
        """SigLIP2 모델로 이미지-텍스트 유사도를 측정한다.

        Args:
            mission_type: 미션 유형.
            image_path: 이미지 파일 경로.
            answer: 미션 정답 키워드.
            prompt_bundle: 모델별 프롬프트 정보.

        Returns:
            모델 투표 결과 딕셔너리.
        """
        from app.models.siglip2 import probe_with_siglip2

        return probe_with_siglip2(mission_type, image_path, answer, prompt_bundle)


class ModelRegistry:
    """싱글턴 모델 레지스트리: VLMProbe 등록/조회."""

    _instance: ModelRegistry | None = None
    _initialized: bool = False

    def __new__(cls) -> ModelRegistry:
        """싱글턴 인스턴스를 반환한다."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """레지스트리를 초기화한다 (최초 1회만 실행)."""
        if self._initialized:
            return
        self._probes: dict[str, VLMProbe] = {}
        self._initialized = True

    @classmethod
    def get_instance(cls) -> ModelRegistry:
        """싱글턴 인스턴스를 반환한다.

        Returns:
            ModelRegistry 싱글턴 인스턴스.
        """
        return cls()

    def register(self, probe: VLMProbe) -> None:
        """VLMProbe를 레지스트리에 등록한다.

        Args:
            probe: 등록할 VLMProbe 인스턴스.
        """
        self._probes[probe.model_name] = probe

    def get(self, name: str) -> VLMProbe:
        """이름으로 VLMProbe를 조회한다.

        Args:
            name: 모델 식별자.

        Returns:
            등록된 VLMProbe 인스턴스.

        Raises:
            ValueError: 해당 이름의 모델이 등록되지 않은 경우.
        """
        name = name.lower().strip()
        if name not in self._probes:
            raise ValueError(
                f"Model '{name}' not registered. Available: {list(self._probes.keys())}"
            )
        return self._probes[name]

    def list_models(self) -> list[str]:
        """등록된 모델 이름 목록을 반환한다.

        Returns:
            모델 이름 문자열 목록.
        """
        return list(self._probes.keys())


def register_default_models() -> None:
    """기본 모델 프로브를 레지스트리에 등록한다."""
    registry = ModelRegistry.get_instance()
    registry.register(_BLIPProbe())
    registry.register(_QwenProbe())
    registry.register(_SigLIP2Probe())
