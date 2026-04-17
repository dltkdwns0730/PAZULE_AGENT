"""Council tiered evaluation aggregator."""

from __future__ import annotations

import logging
from typing import Any

from app.council.judges import (
    BaseJudge,
    ConsistencyJudge,
    JudgeContext,
    JudgeVerdict,
    QwenFallbackJudge,
    ThresholdJudge,
)

logger = logging.getLogger(__name__)


def tiered_evaluate(context: JudgeContext) -> dict[str, Any]:
    """Tier 1 → 2 → 3 순차 실행. needs_escalation=False면 조기 종료.

    Args:
        context: Judge 평가 컨텍스트.

    Returns:
        {approved, confidence, reason, escalated, tier_reached, votes} 딕셔너리.
    """
    tiers: list[BaseJudge] = [
        ConsistencyJudge(),
        ThresholdJudge(),
        QwenFallbackJudge(),
    ]

    verdicts: list[JudgeVerdict] = []
    escalated = False

    for judge in tiers:
        verdict = judge.evaluate(context)
        verdicts.append(verdict)

        if not verdict["needs_escalation"]:
            break
        escalated = True

    final = verdicts[-1]

    return {
        "approved": final["approved"],
        "confidence": final["confidence"],
        "reason": final["reason"],
        "escalated": escalated,
        "tier_reached": len(verdicts),
        "votes": [
            {"judge": v["judge"], "approved": v["approved"], "reason": v["reason"]}
            for v in verdicts
        ],
    }
