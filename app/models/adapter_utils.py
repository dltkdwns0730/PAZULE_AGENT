"""모델 어댑터 유틸리티 모듈.

모델 출력값의 정규화 및 변환 헬퍼 함수를 제공한다.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """점수를 [min_val, max_val] 범위로 클리핑한다.

    Args:
        score: 정규화할 점수.
        min_val: 최솟값 (기본값: 0.0).
        max_val: 최댓값 (기본값: 1.0).

    Returns:
        클리핑된 점수.
    """
    return max(min_val, min(max_val, score))


def build_vote(
    model: str, score: float, label: str, reason: str = ""
) -> dict[str, Any]:
    """표준 투표 결과 딕셔너리를 생성한다.

    Args:
        model: 모델 식별자.
        score: 점수 (0.0 ~ 1.0).
        label: 판정 레이블 ('match' | 'mismatch').
        reason: 판정 이유 (선택).

    Returns:
        표준 투표 결과 딕셔너리.
    """
    return {
        "model": model,
        "score": normalize_score(score),
        "label": label,
        "reason": reason,
    }


def normalize_label(score: float, threshold: float) -> str:
    """점수와 임곗값을 비교해 레이블을 결정한다.

    Args:
        score: 판정 점수.
        threshold: 합격 임곗값.

    Returns:
        'match' 또는 'mismatch'.
    """
    return "match" if score >= threshold else "mismatch"


def text_overlap_score(answer: str, context: str) -> float:
    """answer 단어가 context에 등장하는 비율을 계산한다.

    Args:
        answer: 기준 텍스트 (정답 키워드).
        context: 비교 대상 텍스트.

    Returns:
        0.0 ~ 1.0 사이의 겹침 비율.
    """
    if not answer or not context:
        return 0.0
    answer_words = set(answer.lower().split())
    context_lower = context.lower()
    matched = sum(1 for word in answer_words if word in context_lower)
    return matched / len(answer_words) if answer_words else 0.0
