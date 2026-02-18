"""LangGraph pipeline for mission orchestration."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.council.nodes import (
    coupon_policy_engine,
    decision_engine,
    evidence_aggregator,
    finalizer,
    gate_keeper,
    model_fanout,
    task_router,
)
from app.council.state import PipelineState


def _route_after_gate(state: PipelineState) -> str:
    """Caller: ?? ?? ???? ???
    Purpose: `_route_after_gate` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: state: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    gate_result = state.get("artifacts", {}).get("gate_result", {})
    return "task_router" if gate_result.get("passed") else "finalizer"


def _route_after_decision(state: PipelineState) -> str:
    """Caller: ?? ?? ???? ???
    Purpose: `_route_after_decision` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: state: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    judgment = state.get("artifacts", {}).get("judgment", {})
    return "coupon_policy_engine" if judgment.get("success") else "finalizer"


def build_pipeline():
    """Caller: ?? ?? ???? ???
    Purpose: `build_pipeline` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: None
    Note: ?? ?? ?? ???? ???"""
    workflow = StateGraph(PipelineState)

    workflow.add_node("gate_keeper", gate_keeper)
    workflow.add_node("task_router", task_router)
    workflow.add_node("model_fanout", model_fanout)
    workflow.add_node("evidence_aggregator", evidence_aggregator)
    workflow.add_node("decision_engine", decision_engine)
    workflow.add_node("coupon_policy_engine", coupon_policy_engine)
    workflow.add_node("finalizer", finalizer)

    workflow.set_entry_point("gate_keeper")
    workflow.add_conditional_edges("gate_keeper", _route_after_gate, ["task_router", "finalizer"])
    workflow.add_edge("task_router", "model_fanout")
    workflow.add_edge("model_fanout", "evidence_aggregator")
    workflow.add_edge("evidence_aggregator", "decision_engine")
    workflow.add_conditional_edges(
        "decision_engine", _route_after_decision, ["coupon_policy_engine", "finalizer"]
    )
    workflow.add_edge("coupon_policy_engine", "finalizer")
    workflow.add_edge("finalizer", END)
    return workflow.compile()


pipeline_app = build_pipeline()
