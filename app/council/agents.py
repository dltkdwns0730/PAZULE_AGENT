"""Legacy compatibility shim.

The previous Security/Tech/Design class agents were replaced by the
functional node graph in `app.council.nodes`.
"""

from app.council.nodes import (
    coupon_policy_engine,
    decision_engine,
    evidence_aggregator,
    finalizer,
    gate_keeper,
    model_fanout,
    task_router,
)

__all__ = [
    "gate_keeper",
    "task_router",
    "model_fanout",
    "evidence_aggregator",
    "decision_engine",
    "coupon_policy_engine",
    "finalizer",
]
