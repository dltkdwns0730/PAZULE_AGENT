"""미션 오케스트레이션 그래프의 파이프라인 상태 계약."""

from __future__ import annotations

import operator
from typing import Annotated, Any, NotRequired, TypedDict


class ErrorEvent(TypedDict):
    """파이프라인 실행 중 발생하는 에러 정보 이벤트.

    실패한 노드, 에러 코드, 재시도 가능 여부 등을 기록한다.
    """

    code: str
    message: str
    node: str
    retryable: bool
    model: NotRequired[str]


class ControlFlags(TypedDict, total=False):
    """파이프라인 흐름 제어 플래그.

    강제 종료, 재시도, 수동 검토 필요 여부 등 전역 제어 옵션을 갖는다.
    """

    should_retry: bool
    degrade_mode: bool
    terminate: bool
    manual_review: bool


class RouteDecision(TypedDict):
    """다음 노드 진행 방향 및 라우팅 결정 정보."""

    next_node: str
    reason: str
    confidence: float
    fallback: str


class ModelVote(TypedDict, total=False):
    """개별 비전/언어 모델의 이미지 분석 투표 결과.

    추론 점수(score), 매칭 여부(label), 추론 이유(reason) 등이 포함된다.
    """

    model: str
    mission_type: str
    label: str
    score: float
    confidence: float
    reason: str
    latency_ms: float
    success: bool
    evidence: dict[str, Any]


class PipelineState(TypedDict, total=False):
    """LangGraph 파이프라인 전체를 관통하는 메인 상태 객체.

    이 상태 객체가 노드 간에 전달되며 점진적으로 채워진다.
    """

    request_context: dict[str, Any]
    artifacts: dict[str, Any]
    errors: list[ErrorEvent]
    control_flags: ControlFlags
    route_decision: RouteDecision
    final_response: dict[str, Any]
    messages: Annotated[list[str], operator.add]
