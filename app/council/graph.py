"""LangGraph pipeline for mission orchestration."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.council.deliberation import council
from app.council.nodes import (
    validator,
    router,
    evaluator,
    aggregator,
    judge,
    policy,
    responder,
)
from app.council.state import PipelineState


def _route_after_gate(state: PipelineState) -> str:
    gate_result = state.get("artifacts", {}).get("gate_result", {})
    return "router" if gate_result.get("passed") else "responder"


def _route_after_decision(state: PipelineState) -> str:
    judgment = state.get("artifacts", {}).get("judgment", {})
    return "policy" if judgment.get("success") else "responder"


def build_pipeline():
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
    workflow.add_conditional_edges("validator", _route_after_gate, ["router", "responder"])
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
