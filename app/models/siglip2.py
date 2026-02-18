"""SigLIP2-style probe adapter with lightweight fallback implementation."""

from __future__ import annotations

import time
from typing import Any, Dict

from app.models.adapter_utils import normalize_label, text_overlap_score


def probe_with_siglip2(
    mission_type: str,
    image_path: str,
    answer: str,
    prompt_bundle: Dict[str, Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `probe_with_siglip2` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: mission_type: ???? ???? ??; image_path: ???? ???? ??; answer: ???? ???? ??; prompt_bundle: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    start = time.perf_counter()
    mission = "atmosphere" if mission_type == "photo" else mission_type

    from app.models.blip import get_visual_context

    context = get_visual_context(image_path)
    base = text_overlap_score(answer, context)

    # Atmosphere mission receives stronger weight for SigLIP2-style similarity.
    if mission == "atmosphere":
        score = 0.5 + (0.5 * base)
        threshold = 0.6
    else:
        score = 0.3 + (0.6 * base)
        threshold = 0.68

    score = max(0.0, min(1.0, score))
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    label = normalize_label(score, threshold)

    return {
        "model": "siglip2",
        "mission_type": mission,
        "label": label,
        "score": score,
        "confidence": min(0.92, 0.55 + score * 0.38),
        "reason": "Image-text similarity using fallback SigLIP2 scoring",
        "latency_ms": elapsed_ms,
        "success": True,
        "evidence": {
            "answer": answer,
            "prompt": (prompt_bundle or {}).get("siglip2", {}),
            "context_excerpt": context[:300],
        },
    }
