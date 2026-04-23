import pytest
from app.core.hints import get_atmosphere_hint, ATMOSPHERE_GUIDES, CONTRAST_HINTS
from app.models.prompts import ATMOSPHERE_EN, build_prompt_bundle

def test_atmosphere_en_mapping():
    """5개 분위기 클러스터가 모두 정의되어 있는지 확인"""
    expected_clusters = [
        "화사하고 활기찬", 
        "차분하고 자연적인", 
        "옛스럽고 빈티지한", 
        "웅장하고 신비로운", 
        "동화적이고 장난스러운"
    ]
    for cluster in expected_clusters:
        assert cluster in ATMOSPHERE_EN
        assert len(ATMOSPHERE_EN[cluster]) > 10 # 프롬프트가 충분히 구체적인지 확인

def test_get_atmosphere_hint_contrast():
    """대비 분석 기반 힌트가 정확히 반환되는지 확인"""
    target = "옛스럽고 빈티지한"
    # 화사하고 활기찬 점수가 가장 높을 때
    scores = {
        "화사하고 활기찬": 0.8,
        "차분하고 자연적인": 0.2,
        "옛스럽고 빈티지한": 0.1,
        "웅장하고 신비로운": 0.05,
        "동화적이고 장난스러운": 0.05
    }
    hint = get_atmosphere_hint(target, scores)
    assert hint == CONTRAST_HINTS[(target, "화사하고 활기찬")]
    assert "너무 밝고 현대적인 느낌" in hint

def test_get_atmosphere_hint_fallback():
    """대비 힌트가 없을 때 일반 가이드가 반환되는지 확인"""
    target = "웅장하고 신비로운"
    scores = {
        "화사하고 활기찬": 0.1,
        "웅장하고 신비로운": 0.2 # 타겟 점수가 낮음
    }
    hint = get_atmosphere_hint(target, scores)
    assert any(h in hint for h in ATMOSPHERE_GUIDES[target])

def test_build_prompt_bundle_new_clusters():
    """새로운 클러스터에 대해 프롬프트 번들이 잘 생성되는지 확인"""
    cluster = "동화적이고 장난스러운"
    bundle = build_prompt_bundle("atmosphere", cluster)
    assert bundle["answer_en"] == ATMOSPHERE_EN[cluster]
    assert "whimsical" in bundle["siglip2_candidates"][0]
