"""LangGraph 기반 미션 오케스트레이션 파이프라인 빌더."""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from app.council.deliberation import council
from app.council.nodes import (
    aggregator,
    evaluator,
    judge,
    policy,
    responder,
    router,
    validator,
)
from app.council.state import PipelineState

logger = logging.getLogger(__name__)


def _route_after_gate(state: PipelineState) -> str:
    """게이트 통과 여부에 따라 다음 노드를 결정한다.

    Args:
        state: 현재 파이프라인 상태.

    Returns:
        'router' 또는 'responder'.
    """
    gate_result = state.get("artifacts", {}).get("gate_result", {})
    return "router" if gate_result.get("passed") else "responder"


def _route_after_decision(state: PipelineState) -> str:
    """판정 결과에 따라 다음 노드를 결정한다.

    Args:
        state: 현재 파이프라인 상태.

    Returns:
        'policy' 또는 'responder'.
    """
    judgment = state.get("artifacts", {}).get("judgment", {})
    return "policy" if judgment.get("success") else "responder"


def _should_run_council(state: PipelineState) -> str:
    """앙상블 결과에 따라 교차 검증(Council) 실행 여부를 결정한다.

    Args:
        state: 현재 파이프라인 상태.

    Returns:
        'council' (경계값/충돌 시) 또는 'judge' (확정적일 때).
    """
    from app.core.config import settings

    artifacts = state.get("artifacts", {})
    ensemble = artifacts.get("ensemble_result", {})

    conflict = bool(ensemble.get("conflict"))
    merged_score = float(ensemble.get("merged_score", 0.0))
    threshold = float(ensemble.get("threshold", 0.7))
    margin = float(settings.COUNCIL_BORDERLINE_MARGIN)

    # 1. 모델 간 이견(Conflict)이 있는 경우 에스컬레이션
    if conflict:
        logger.info("[graph] 모델 간 충돌 감지 → Council 에스컬레이션")
        return "council"

    # 2. 점수가 경계값(Borderline)인 경우 에스컬레이션
    is_borderline = (threshold - margin) <= merged_score <= (threshold + margin)
    if is_borderline:
        logger.info(
            "[graph] 경계값 점수(%.4f) 감지 (Threshold: %s, Margin: %s) → Council 에스컬레이션",
            merged_score,
            threshold,
            margin,
        )
        return "council"

    # 3. 확정적인 결과인 경우 바로 심판 노드로 이동
    return "judge"


def build_pipeline() -> StateGraph:
    """파이프라인 그래프를 빌드하고 컴파일된 앱을 반환한다.

    Returns:
        컴파일된 LangGraph StateGraph 앱.
    """
    workflow = StateGraph(PipelineState)

    workflow.add_node("validator", validator)
    workflow.add_node("router", router)
    workflow.add_node("evaluator", evaluator)
    workflow.add_node("aggregator", aggregator)
    workflow.add_node("council", council)
    workflow.add_node("judge", judge)
    workflow.add_node("policy", policy)
    workflow.add_node("responder", responder)

    workflow.set_entry_point("validator")
    workflow.add_conditional_edges(
        "validator", _route_after_gate, ["router", "responder"]
    )
    workflow.add_edge("router", "evaluator")
    workflow.add_edge("evaluator", "aggregator")

    # [Optimization] aggregator -> council (conditional) -> judge
    workflow.add_conditional_edges(
        "aggregator", _should_run_council, ["council", "judge"]
    )
    workflow.add_edge("council", "judge")
    workflow.add_conditional_edges(
        "judge", _route_after_decision, ["policy", "responder"]
    )
    workflow.add_edge("policy", "responder")
    workflow.add_edge("responder", END)
    return workflow.compile()


pipeline_app = build_pipeline()
