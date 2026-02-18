"""Qwen-VL style adapter.

This module uses an LLM-compatible JSON judging prompt as a practical adapter.
If no API key is configured, it falls back to deterministic token similarity.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.models.adapter_utils import normalize_label, safe_json_loads, text_overlap_score


def _fallback_vote(
    mission: str, answer: str, context: str, prompt_bundle: Dict[str, Dict[str, str]]
) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `_fallback_vote` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: mission: ???? ???? ??; answer: ???? ???? ??; context: ???? ???? ??; prompt_bundle: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    base = text_overlap_score(answer, context)
    if mission == "location":
        score = 0.4 + 0.5 * base
        threshold = 0.68
    else:
        score = 0.48 + 0.5 * base
        threshold = 0.6

    score = max(0.0, min(1.0, score))
    return {
        "label": normalize_label(score, threshold),
        "score": score,
        "confidence": min(0.9, 0.5 + score * 0.4),
        "reason": "Fallback Qwen probe using context-text alignment",
        "evidence": {
            "answer": answer,
            "prompt": prompt_bundle.get("qwen", {}),
            "context_excerpt": context[:320],
        },
    }


def probe_with_qwen(
    mission_type: str,
    image_path: str,
    answer: str,
    prompt_bundle: Dict[str, Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `probe_with_qwen` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: mission_type: ???? ???? ??; image_path: ???? ???? ??; answer: ???? ???? ??; prompt_bundle: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    start = time.perf_counter()
    mission = "atmosphere" if mission_type == "photo" else mission_type
    prompts = prompt_bundle or {}
    from app.models.blip import get_visual_context

    context = get_visual_context(image_path)

    if not settings.OPENAI_API_KEY:
        vote = _fallback_vote(mission, answer, context, prompts)
        return {
            "model": "qwen",
            "mission_type": mission,
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "success": True,
            **vote,
        }

    system_prompt = prompts.get("qwen", {}).get(
        "system",
        "You are a visual mission judge. Return strict JSON only.",
    )
    user_prompt = prompts.get("qwen", {}).get(
        "user",
        "Judge alignment between target and image context.",
    )

    chain = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "user",
                (
                    f"{user_prompt}\n\n"
                    f"mission_type={mission}\n"
                    f"target={answer}\n"
                    f"context={context}\n\n"
                    'Return JSON: {"label":"match|mismatch","score":0..1,'
                    '"confidence":0..1,"reason":"..."}'
                ),
            ),
        ]
    ) | ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=settings.OPENAI_API_KEY)

    try:
        raw = chain.invoke({}).content
        parsed = safe_json_loads(raw)
    except Exception as exc:
        parsed = {
            "label": "mismatch",
            "score": 0.35,
            "confidence": 0.4,
            "reason": f"Qwen probe failed: {exc}",
        }

    score = float(parsed.get("score", 0.0))
    score = max(0.0, min(1.0, score))
    label = parsed.get("label") or normalize_label(score, 0.6)
    confidence = float(parsed.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))

    return {
        "model": "qwen",
        "mission_type": mission,
        "label": label,
        "score": score,
        "confidence": confidence,
        "reason": parsed.get("reason", "Qwen-style probe result"),
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        "success": True,
        "evidence": {
            "answer": answer,
            "prompt": prompts.get("qwen", {}),
            "context_excerpt": context[:320],
        },
    }
