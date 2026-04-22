import pytest
from app.models.model_registry import ModelRegistry, register_default_models
from app.models.prompts import build_prompt_bundle, _to_english


def test_model_registry_singleton():
    r1 = ModelRegistry.get_instance()
    r2 = ModelRegistry.get_instance()
    assert r1 is r2


def test_register_and_get_model():
    registry = ModelRegistry.get_instance()
    # 기존 모델 초기화 (테스트 격리를 위해 리셋은 어려우나 추가 등록은 가능)
    from app.models.base import VLMProbe

    class MockProbe(VLMProbe):
        @property
        def model_name(self) -> str:
            return "mock_vlm"

        def probe(self, *args, **kwargs):
            return {"score": 1.0}

    registry.register(MockProbe())
    assert "mock_vlm" in registry.list_models()
    assert registry.get("mock_vlm").model_name == "mock_vlm"


def test_get_unregistered_model():
    registry = ModelRegistry.get_instance()
    with pytest.raises(ValueError, match="not registered"):
        registry.get("nonexistent_model")


def test_register_default_models():
    register_default_models()
    registry = ModelRegistry.get_instance()
    models = registry.list_models()
    assert "blip" in models
    assert "qwen" in models
    assert "siglip2" in models


def test_build_prompt_bundle_location():
    bundle = build_prompt_bundle("location", "활돌이")
    assert bundle["mission_type"] == "location"
    assert "pink cartoon character" in bundle["answer_en"]
    assert "Is this a photo of" in bundle["blip_question"]
    assert "siglip2_candidates" in bundle


def test_build_prompt_bundle_atmosphere():
    bundle = build_prompt_bundle("atmosphere", "차분한")
    assert bundle["mission_type"] == "atmosphere"
    assert "calm and peaceful" in bundle["answer_en"]
    assert "atmosphere?" in bundle["blip_question"]


def test_to_english_fallback():
    # 매핑에 없는 단어는 그대로 반환
    assert _to_english("unknown_word", "location") == "unknown_word"
    assert _to_english("unknown_word", "atmosphere") == "unknown_word"
