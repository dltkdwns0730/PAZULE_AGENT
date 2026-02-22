"""프롬프트 번들 생성 모듈.

미션 유형별 모델 프롬프트를 구성한다.
"""

from __future__ import annotations

from typing import Any, Dict


def build_prompt_bundle(mission_type: str, answer: str | None = None) -> Dict[str, Any]:
    """미션 유형과 정답 기반으로 프롬프트 번들을 생성한다.

    Args:
        mission_type: 미션 유형 ('location' | 'atmosphere')
        answer: 미션 정답 키워드

    Returns:
        모델별 프롬프트 정보가 담긴 딕셔너리
    """
    answer = answer or "unknown"

    if mission_type == "location":
        return {
            "mission_type": mission_type,
            "answer": answer,
            "blip_question": f"Is this a photo of {answer}?",
            "qwen_prompt": f"이 이미지가 '{answer}' 장소를 보여주는지 판단해 주세요.",
            "siglip2_candidates": [
                f"a photo of {answer}",
                "a photo of a different place",
            ],
        }

    return {
        "mission_type": mission_type,
        "answer": answer,
        "blip_question": f"Does this image convey a {answer} atmosphere?",
        "qwen_prompt": f"이 이미지에서 '{answer}' 분위기가 느껴지는지 판단해 주세요.",
        "siglip2_candidates": [
            f"a {answer} atmosphere",
            "a different atmosphere",
        ],
    }
