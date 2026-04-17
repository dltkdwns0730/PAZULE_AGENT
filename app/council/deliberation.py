"""Council deliberation node for the pipeline graph."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.council.aggregator import tiered_evaluate
from app.council.judges import JudgeContext

logger = logging.getLogger(__name__)


def council(state: dict[str, Any]) -> dict[str, Any]:
    """위원회 판정 노드: tiered_evaluate 실행 후 artifacts에 council_verdict를 저장한다.

    config.COUNCIL_ENABLED=False이면 패스스루 (verdict 없이 다음 노드로 진행).

    Args:
        state: 파이프라인 전체 상태 딕셔너리.

    Returns:
        artifacts와 messages가 갱신된 상태 딕셔너리.
    """
    artifacts = dict(state.get("artifacts", {}))

    if not getattr(settings, "COUNCIL_ENABLED", True):
        logger.debug("council: disabled (passthrough)")
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
    logger.debug("council: tier=%s, approved=%s", tier, approved)
    return {
        "artifacts": artifacts,
        "messages": [f"council: tier={tier}, approved={approved}"],
    }
