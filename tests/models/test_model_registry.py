"""ModelRegistry 단위 테스트.

검증 대상:
  - ModelRegistry 싱글턴 동작
  - register / get / list_models
  - get — 미등록 모델 ValueError
  - _BLIPProbe / _QwenProbe / _SigLIP2Probe model_name 및 probe 라우팅
  - register_default_models
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.models.model_registry import ModelRegistry, register_default_models
from app.models.base import VLMProbe


# ── 격리 픽스처 ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def fresh_registry():
    """각 테스트마다 싱글턴 상태를 초기화한다."""
    original_instance = ModelRegistry._instance
    original_initialized = ModelRegistry._initialized

    ModelRegistry._instance = None
    ModelRegistry._initialized = False

    yield

    ModelRegistry._instance = original_instance
    ModelRegistry._initialized = original_initialized


# ── 싱글턴 ────────────────────────────────────────────────────────────────────


class TestSingleton:
    def test_get_instance_returns_same_object(self) -> None:
        a = ModelRegistry.get_instance()
        b = ModelRegistry.get_instance()
        assert a is b

    def test_new_returns_same_object(self) -> None:
        a = ModelRegistry()
        b = ModelRegistry()
        assert a is b

    def test_init_runs_once(self) -> None:
        registry = ModelRegistry.get_instance()
        registry.register(MagicMock(model_name="dummy"))
        # 두 번째 init은 _probes를 초기화하지 않아야 함
        ModelRegistry.__init__(registry)
        assert "dummy" in registry.list_models()


# ── register / get / list_models ─────────────────────────────────────────────


class TestRegisterGetList:
    def _make_probe(self, name: str) -> VLMProbe:
        probe = MagicMock(spec=VLMProbe)
        probe.model_name = name
        return probe

    def test_register_and_get(self) -> None:
        registry = ModelRegistry.get_instance()
        probe = self._make_probe("test_model")
        registry.register(probe)
        assert registry.get("test_model") is probe

    def test_get_case_insensitive(self) -> None:
        registry = ModelRegistry.get_instance()
        probe = self._make_probe("siglip2")
        registry.register(probe)
        assert registry.get("SigLIP2") is probe

    def test_get_strips_whitespace(self) -> None:
        registry = ModelRegistry.get_instance()
        probe = self._make_probe("blip")
        registry.register(probe)
        assert registry.get("  blip  ") is probe

    def test_get_unregistered_raises_value_error(self) -> None:
        registry = ModelRegistry.get_instance()
        with pytest.raises(ValueError, match="not registered"):
            registry.get("unknown_model")

    def test_list_models_empty(self) -> None:
        registry = ModelRegistry.get_instance()
        assert registry.list_models() == []

    def test_list_models_returns_registered_names(self) -> None:
        registry = ModelRegistry.get_instance()
        registry.register(self._make_probe("alpha"))
        registry.register(self._make_probe("beta"))
        names = registry.list_models()
        assert "alpha" in names
        assert "beta" in names

    def test_register_overwrite(self) -> None:
        registry = ModelRegistry.get_instance()
        probe1 = self._make_probe("model")
        probe2 = self._make_probe("model")
        registry.register(probe1)
        registry.register(probe2)
        assert registry.get("model") is probe2


# ── _BLIPProbe ────────────────────────────────────────────────────────────────


class TestBLIPProbe:
    def _get_blip_probe(self):
        from app.models.model_registry import _BLIPProbe

        return _BLIPProbe()

    def test_model_name(self) -> None:
        probe = self._get_blip_probe()
        assert probe.model_name == "blip"

    def test_probe_location_calls_probe_with_blip_location(self) -> None:
        probe = self._get_blip_probe()
        mock_result = {"score": 0.8, "label": "match"}
        with patch(
            "app.models.blip.probe_with_blip_location", return_value=mock_result
        ) as m:
            result = probe.probe("location", "/img.jpg", "answer", {})
        m.assert_called_once_with("/img.jpg", "answer", {})
        assert result == mock_result

    def test_probe_atmosphere_calls_probe_with_blip_atmosphere(self) -> None:
        probe = self._get_blip_probe()
        mock_result = {"score": 0.7, "label": "mismatch"}
        with patch(
            "app.models.blip.probe_with_blip_atmosphere", return_value=mock_result
        ) as m:
            result = probe.probe("atmosphere", "/img.jpg", "calm", {})
        m.assert_called_once_with("/img.jpg", "calm", {})
        assert result == mock_result


# ── _QwenProbe ────────────────────────────────────────────────────────────────


class TestQwenProbe:
    def _get_qwen_probe(self):
        from app.models.model_registry import _QwenProbe

        return _QwenProbe()

    def test_model_name(self) -> None:
        probe = self._get_qwen_probe()
        assert probe.model_name == "qwen"

    def test_probe_delegates_to_probe_with_qwen(self) -> None:
        probe = self._get_qwen_probe()
        mock_result = {"score": 0.9}
        with patch("app.models.qwen_vl.probe_with_qwen", return_value=mock_result) as m:
            result = probe.probe("location", "/img.jpg", "target", {"bundle": "x"})
        m.assert_called_once_with("location", "/img.jpg", "target", {"bundle": "x"})
        assert result == mock_result


# ── _SigLIP2Probe ─────────────────────────────────────────────────────────────


class TestSigLIP2Probe:
    def _get_siglip2_probe(self):
        from app.models.model_registry import _SigLIP2Probe

        return _SigLIP2Probe()

    def test_model_name(self) -> None:
        probe = self._get_siglip2_probe()
        assert probe.model_name == "siglip2"

    def test_probe_delegates_to_probe_with_siglip2(self) -> None:
        probe = self._get_siglip2_probe()
        mock_result = {"score": 0.85}
        with patch(
            "app.models.siglip2.probe_with_siglip2", return_value=mock_result
        ) as m:
            result = probe.probe("atmosphere", "/img.jpg", "화사한", {"bundle": "y"})
        m.assert_called_once_with("atmosphere", "/img.jpg", "화사한", {"bundle": "y"})
        assert result == mock_result


# ── register_default_models ───────────────────────────────────────────────────


class TestRegisterDefaultModels:
    def test_registers_blip_qwen_siglip2(self) -> None:
        register_default_models()
        registry = ModelRegistry.get_instance()
        names = registry.list_models()
        assert "blip" in names
        assert "qwen" in names
        assert "siglip2" in names

    def test_get_blip_after_register_default(self) -> None:
        register_default_models()
        registry = ModelRegistry.get_instance()
        probe = registry.get("blip")
        assert probe.model_name == "blip"
