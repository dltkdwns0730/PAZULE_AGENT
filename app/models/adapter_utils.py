"""모델 어댑터 유틸리티 모듈 (스텁).

모델 출력값의 정규화 및 변환 헬퍼.
"""

from __future__ import annotations

from typing import Any, Dict


def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """점수를 [0, 1] 범위로 정규화한다."""
    return max(min_val, min(max_val, score))


def build_vote(
    model: str, score: float, label: str, reason: str = ""
) -> Dict[str, Any]:
    """표준 투표 결과 딕셔너리를 생성한다."""
    return {
        "model": model,
        "score": normalize_score(score),
        "label": label,
        "reason": reason,
    }
