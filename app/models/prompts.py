"""프롬프트 번들 생성 모듈.

미션 유형별 모델 프롬프트를 구성한다.
VLM 프롬프트는 영어로 작성 — 한국어 프롬프트 대비 score 3~4배 향상 (벤치마크 확인).
"""

from __future__ import annotations

from typing import Any, Dict

# 한국어 랜드마크명 → 영어 descriptive 프롬프트 변환
LANDMARK_EN: Dict[str, str] = {
    "활판공방 인쇄기": "an outdoor sculpture of a vintage printing press covered in metal type blocks",
    "활돌이": "a pink cartoon character mascot statue",
    "마법천자문 손오공": "a colorful monkey boy statue with spiky red hair in purple clothes",
    "나남출판사": "a building covered in green ivy",
    "지혜의숲 조각상": "a large sculpture at the entrance of a book library",
    "지혜의숲 고양이": "a cat sculpture in a glass display case",
    "지혜의숲 입구 조각상": "a group of standing figure sculptures near a library entrance",
    "네모탑": "a tall square tower sculpture",
    "창틀 피노키오": "a wooden pinocchio puppet sitting on a window frame",
    "피노지움 조각상": "a pinocchio scene sculpture with characters and books",
    "로드킬 부엉이": "an owl sculpture made of recycled tires",
}

# 한국어 분위기 키워드 → 영어 변환
ATMOSPHERE_EN: Dict[str, str] = {
    "차분한": "calm and peaceful",
    "화사한": "bright and colorful",
    "활기찬": "lively and energetic",
    "옛스러운": "old-fashioned and vintage",
    "자연적인": "natural and scenic",
    "신비로운": "mysterious and dreamy",
    "웅장한": "grand and majestic",
}


def _to_english(answer: str, mission_type: str) -> str:
    """한국어 answer를 영어로 변환한다. 매핑에 없으면 원본 반환."""
    if mission_type == "location":
        return LANDMARK_EN.get(answer, answer)
    return ATMOSPHERE_EN.get(answer, answer)


def build_prompt_bundle(mission_type: str, answer: str | None = None) -> Dict[str, Any]:
    """미션 유형과 정답 기반으로 프롬프트 번들을 생성한다.

    Args:
        mission_type: 미션 유형 ('location' | 'atmosphere')
        answer: 미션 정답 키워드 (한국어)

    Returns:
        모델별 프롬프트 정보가 담긴 딕셔너리
    """
    answer = answer or "unknown"
    answer_en = _to_english(answer, mission_type)

    if mission_type == "location":
        return {
            "mission_type": mission_type,
            "answer": answer,
            "answer_en": answer_en,
            "blip_question": f"Is this a photo of {answer_en}?",
            "qwen_prompt": (
                f"Determine whether this image shows the following landmark: {answer_en}. "
                f"Respond with a confidence score between 0 and 1."
            ),
            "siglip2_candidates": [
                f"a photo of {answer_en}",
                "a photo of a different place",
            ],
        }

    return {
        "mission_type": mission_type,
        "answer": answer,
        "answer_en": answer_en,
        "blip_question": f"Does this image convey a {answer_en} atmosphere?",
        "qwen_prompt": (
            f"Determine whether this image conveys a {answer_en} atmosphere. "
            f"Respond with a confidence score between 0 and 1."
        ),
        "siglip2_candidates": [
            f"a photo with {answer_en} atmosphere",
            "a photo with a different atmosphere",
        ],
    }
