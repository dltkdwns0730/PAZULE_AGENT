"""Council tiered evaluation aggregator."""

from __future__ import annotations

from typing import Any, Dict, List

from app.council.judges import (
    BaseJudge,
    ConsistencyJudge,
    JudgeContext,
    JudgeVerdict,
    QwenFallbackJudge,
    ThresholdJudge,
)


def tiered_evaluate(context: JudgeContext) -> Dict[str, Any]:
    """Tier 1 → 2 → 3 순차 실행. needs_escalation=False면 조기 종료.

    Returns:
        {approved, confidence, reason, escalated, votes}
    """
    tiers: List[BaseJudge] = [
        ConsistencyJudge(),
        ThresholdJudge(),
        QwenFallbackJudge(),
    ]

    verdicts: List[JudgeVerdict] = []
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
