"""CLIP 스타일 프로브 어댑터 (graceful fallback 포함)."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.models.adapter_utils import normalize_label, text_overlap_score

logger = logging.getLogger(__name__)


def probe_with_clip(
    mission_type: str,
    image_path: str,
    answer: str,
    prompt_bundle: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    """CLIP 폴백 프로브로 이미지-텍스트 유사도를 측정한다.

    실제 CLIP 모델 대신 BLIP 시각 컨텍스트를 이용한 텍스트 겹침 방식으로
    유사도 점수를 추정한다.

    Args:
        mission_type: 미션 유형 ('location' | 'atmosphere' | 'photo').
        image_path: 분석할 이미지 파일 경로.
        answer: 미션 정답 키워드.
        prompt_bundle: 모델별 프롬프트 정보 딕셔너리 (선택).

    Returns:
        모델 투표 결과 딕셔너리.
    """
    start = time.perf_counter()
    mission = "atmosphere" if mission_type == "photo" else mission_type

    from app.models.blip import get_visual_context

    context = get_visual_context(image_path)
    base = text_overlap_score(answer, context)

    if mission == "location":
        score = 0.35 + (0.65 * base)
    else:
        score = 0.45 + (0.55 * base)

    score = max(0.0, min(1.0, score))
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    label = normalize_label(score, 0.62 if mission == "atmosphere" else 0.68)

    return {
        "model": "clip",
        "mission_type": mission,
        "label": label,
        "score": score,
        "confidence": min(0.9, 0.5 + score * 0.4),
        "reason": "Context-token similarity (fallback CLIP probe)",
        "latency_ms": elapsed_ms,
        "success": True,
        "evidence": {
            "answer": answer,
            "prompt": (prompt_bundle or {}).get("clip", {}),
            "context_excerpt": context[:300],
        },
    }
