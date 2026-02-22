"""Pipeline state contracts for the mission orchestration graph."""

import operator
from typing import Annotated, Any, Dict, List, NotRequired, TypedDict


class ErrorEvent(TypedDict):
    """파이프라인 실행 중 발생하는 에러 정보를 담는 이벤트 객체.
    실패한 노드, 에러 코드, 재시도 가능 여부 등을 기록합니다."""
    code: str
    message: str
    node: str
    retryable: bool
    model: NotRequired[str]


class ControlFlags(TypedDict, total=False):
    """파이프라인 흐름 제어를 위한 플래그들.
    강제 종료, 재시도, 수동 검토 필요 여부 등 전역 제어 옵션을 갖습니다."""
    should_retry: bool
    degrade_mode: bool
    terminate: bool
    manual_review: bool


class RouteDecision(TypedDict):
    """다음 노드 진행 방향 및 라우팅 결정 사항을 담는 객체."""
    next_node: str
    reason: str
    confidence: float
    fallback: str


class ModelVote(TypedDict, total=False):
    """개별 비전/언어 모델이 이미지를 분석하고 산출한 투표 결과 객체.
    추론 점수(score), 매칭 여부(label), 추론 이유(reason) 등이 포함됩니다."""
    model: str
    mission_type: str
    label: str
    score: float
    confidence: float
    reason: str
    latency_ms: float
    success: bool
    evidence: Dict[str, Any]


class PipelineState(TypedDict, total=False):
    """LangGraph 파이프라인 전체를 관통하는 메인 스코프 객체(State).
    이 상태 객체가 노드 간에 전달되며 점진적으로 채워집니다."""
    request_context: Dict[str, Any]
    artifacts: Dict[str, Any]
    errors: List[ErrorEvent]
    control_flags: ControlFlags
    route_decision: RouteDecision
    final_response: Dict[str, Any]
    messages: Annotated[List[str], operator.add]
