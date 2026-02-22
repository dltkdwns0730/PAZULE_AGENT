"""Council deliberation node for the pipeline graph."""

from __future__ import annotations

from typing import Any, Dict

from app.core.config import settings
from app.council.aggregator import tiered_evaluate
from app.council.judges import JudgeContext


def council(state: Dict[str, Any]) -> Dict[str, Any]:
    """[위원회] tiered_evaluate 실행 → artifacts에 council_verdict 저장.

    config.COUNCIL_ENABLED=False이면 패스스루 (verdict 없이 다음 노드로).
    """
    artifacts = dict(state.get("artifacts", {}))

    if not getattr(settings, "COUNCIL_ENABLED", True):
        return {
            "artifacts": artifacts,
            "messages": ["council: disabled (passthrough)"],
        }

    ensemble_result = artifacts.get("ensemble_result", {})
    model_votes = artifacts.get("model_votes", [])
    request_context = dict(state.get("request_context", {}))

    context = JudgeContext(
        mission_type=request_context.get("mission_type", "location"),
        ensemble_result=ensemble_result,
        model_votes=model_votes,
        request_context=request_context,
    )

    verdict = tiered_evaluate(context)
    artifacts["council_verdict"] = verdict

    tier = verdict.get("tier_reached", 0)
    approved = verdict.get("approved", False)
    return {
        "artifacts": artifacts,
        "messages": [
            f"council: tier={tier}, approved={approved}"
        ],
    }
