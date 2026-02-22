"""Model registry: VLMProbe registration and lookup."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.models.base import VLMProbe


class _BLIPProbe(VLMProbe):
    @property
    def model_name(self) -> str:
        return "blip"

    def probe(self, mission_type, image_path, answer, prompt_bundle) -> Dict[str, Any]:
        from app.models.blip import probe_with_blip_atmosphere, probe_with_blip_location

        if mission_type == "location":
            return probe_with_blip_location(image_path, answer, prompt_bundle)
        return probe_with_blip_atmosphere(image_path, answer, prompt_bundle)


class _QwenProbe(VLMProbe):
    @property
    def model_name(self) -> str:
        return "qwen"

    def probe(self, mission_type, image_path, answer, prompt_bundle) -> Dict[str, Any]:
        from app.models.qwen_vl import probe_with_qwen

        return probe_with_qwen(mission_type, image_path, answer, prompt_bundle)



class _SigLIP2Probe(VLMProbe):
    @property
    def model_name(self) -> str:
        return "siglip2"

    def probe(self, mission_type, image_path, answer, prompt_bundle) -> Dict[str, Any]:
        from app.models.siglip2 import probe_with_siglip2

        return probe_with_siglip2(mission_type, image_path, answer, prompt_bundle)


class ModelRegistry:
    """싱글턴 모델 레지스트리: VLMProbe 등록/조회."""

    _instance: Optional[ModelRegistry] = None
    _initialized: bool = False

    def __new__(cls) -> ModelRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._probes: Dict[str, VLMProbe] = {}
        self._initialized = True

    @classmethod
    def get_instance(cls) -> ModelRegistry:
        return cls()

    def register(self, probe: VLMProbe) -> None:
        self._probes[probe.model_name] = probe

    def get(self, name: str) -> VLMProbe:
        name = name.lower().strip()
        if name not in self._probes:
            raise ValueError(f"Model '{name}' not registered. Available: {list(self._probes.keys())}")
        return self._probes[name]

    def list_models(self) -> list[str]:
        return list(self._probes.keys())


def register_default_models() -> None:
    """기본 모델 프로브를 레지스트리에 등록한다."""
    registry = ModelRegistry.get_instance()
    registry.register(_BLIPProbe())
    registry.register(_QwenProbe())
    registry.register(_SigLIP2Probe())
