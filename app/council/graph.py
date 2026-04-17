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
    workflow.add_edge("aggregator", "council")
    workflow.add_edge("council", "judge")
    workflow.add_conditional_edges(
        "judge", _route_after_decision, ["policy", "responder"]
    )
    workflow.add_edge("policy", "responder")
    workflow.add_edge("responder", END)
    return workflow.compile()


pipeline_app = build_pipeline()
