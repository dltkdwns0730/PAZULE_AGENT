"""CLIP-style probe adapter with graceful fallback."""

from __future__ import annotations

import time
from typing import Any, Dict

from app.models.adapter_utils import normalize_label, text_overlap_score


def probe_with_clip(
    mission_type: str,
    image_path: str,
    answer: str,
    prompt_bundle: Dict[str, Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `probe_with_clip` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: mission_type: ???? ???? ??; image_path: ???? ???? ??; answer: ???? ???? ??; prompt_bundle: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    start = time.perf_counter()
    mission = "atmosphere" if mission_type == "photo" else mission_type

    # Fallback probe: use visual context text as pseudo embedding corpus.
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
