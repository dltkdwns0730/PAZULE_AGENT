"""Council Judge 구현체: ConsistencyJudge, ThresholdJudge, QwenFallbackJudge."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, TypedDict

from app.core.config import settings

logger = logging.getLogger(__name__)


class JudgeContext(TypedDict):
    """Judge 평가에 필요한 컨텍스트 정보."""

    mission_type: str
    ensemble_result: dict[str, Any]
    model_votes: list[dict[str, Any]]
    request_context: dict[str, Any]


class JudgeVerdict(TypedDict):
    """Judge 평가 결과."""

    judge: str
    approved: bool
    confidence: float
    reason: str
    needs_escalation: bool


class BaseJudge(ABC):
    """추상 Judge 기반 클래스."""

    @abstractmethod
    def evaluate(self, context: JudgeContext) -> JudgeVerdict:
        """평가를 수행하고 판정 결과를 반환한다.

        Args:
            context: Judge 평가 컨텍스트.

        Returns:
            판정 결과 딕셔너리.
        """
        ...


class ConsistencyJudge(BaseJudge):
    """Tier 1: 규칙 기반 필드 일관성 검증 (API 호출 없음)."""

    def evaluate(self, context: JudgeContext) -> JudgeVerdict:
        """ensemble_result와 model_votes의 일관성을 검증한다.

        Args:
            context: Judge 평가 컨텍스트.

        Returns:
            일관성 검증 판정 결과.
        """
        ensemble = context["ensemble_result"]
        votes = context["model_votes"]

        merged_score = float(ensemble.get("merged_score", 0.0))
        merged_label = ensemble.get("merged_label", "mismatch")
        threshold = float(ensemble.get("threshold", 1.0))

        issues: list[str] = []

        if merged_score >= threshold and merged_label == "mismatch":
            issues.append("score >= threshold but label is mismatch")
        if merged_score < threshold and merged_label == "match":
            issues.append("score < threshold but label is match")
        if not votes and merged_score > 0:
            issues.append("no model votes but score > 0")

        if issues:
            return JudgeVerdict(
                judge="ConsistencyJudge",
                approved=False,
                confidence=0.3,
                reason=f"Inconsistencies found: {'; '.join(issues)}",
                needs_escalation=True,
            )

        return JudgeVerdict(
            judge="ConsistencyJudge",
            approved=True,
            confidence=0.9,
            reason="All fields consistent",
            needs_escalation=False,
        )


class ThresholdJudge(BaseJudge):
    """Tier 2: 규칙 기반 경계값/충돌 검증 (API 호출 없음)."""

    def evaluate(self, context: JudgeContext) -> JudgeVerdict:
        """점수 경계값과 모델 충돌 여부를 검증한다.

        Args:
            context: Judge 평가 컨텍스트.

        Returns:
            경계값/충돌 검증 판정 결과.
        """
        ensemble = context["ensemble_result"]
        margin = getattr(settings, "COUNCIL_BORDERLINE_MARGIN", 0.08)

        merged_score = float(ensemble.get("merged_score", 0.0))
        threshold = float(ensemble.get("threshold", 1.0))
        conflict = bool(ensemble.get("conflict", False))

        distance = abs(merged_score - threshold)
        is_borderline = distance <= margin

        if conflict:
            return JudgeVerdict(
                judge="ThresholdJudge",
                approved=False,
                confidence=0.4,
                reason=f"Model conflict detected, score={merged_score:.4f}",
                needs_escalation=True,
            )

        if is_borderline:
            return JudgeVerdict(
                judge="ThresholdJudge",
                approved=merged_score >= threshold,
                confidence=0.5,
                reason=f"Borderline score: {merged_score:.4f} (threshold={threshold}, margin={margin})",
                needs_escalation=True,
            )

        approved = merged_score >= threshold
        return JudgeVerdict(
            judge="ThresholdJudge",
            approved=approved,
            confidence=0.95 if distance > margin * 2 else 0.8,
            reason=f"Clear {'pass' if approved else 'fail'}: score={merged_score:.4f}, threshold={threshold}",
            needs_escalation=False,
        )


class QwenFallbackJudge(BaseJudge):
    """Tier 3: 조건부 Qwen-VL 심사 (borderline/conflict일 때만 무거운 VLM 단발 호출)."""

    def evaluate(self, context: JudgeContext) -> JudgeVerdict:
        """Qwen-VL을 호출해 최종 판정을 수행한다.

        Args:
            context: Judge 평가 컨텍스트.

        Returns:
            Qwen-VL 기반 판정 결과. 호출 실패 시 ensemble 결과로 폴백.
        """
        from app.models.model_registry import ModelRegistry
        from app.models.prompts import build_prompt_bundle

        ensemble = context["ensemble_result"]
        req = context["request_context"]
        mission_type = req.get("mission_type", "location")
        image_path = req.get("image_path")
        answer = req.get("answer")

        try:
            logger.info(
                "[Council] SigLIP2의 1차 판단이 모호하여, Qwen-VL(LLM)을 추가 호출합니다..."
            )
            registry = ModelRegistry.get_instance()
            probe = registry.get("qwen")
            prompt_bundle = build_prompt_bundle(mission_type, answer)

            qwen_vote = probe.probe(mission_type, image_path, answer, prompt_bundle)

            qwen_score = qwen_vote.get("score", 0.0)
            threshold = float(ensemble.get("threshold", 1.0))
            approved = qwen_score >= threshold

            logger.info("[Council] 추가 모델(Qwen) 판정 완료. Score: %.2f", qwen_score)

            return JudgeVerdict(
                judge="QwenFallbackJudge",
                approved=approved,
                confidence=qwen_score,
                reason=f"Qwen-VL Fallback Override (Original score was borderline): {qwen_vote.get('reason', '')}",
                needs_escalation=False,
            )
        except Exception as exc:
            logger.error("[QwenFallbackJudge] Error: %s", exc)
            merged_score = float(ensemble.get("merged_score", 0.0))
            threshold = float(ensemble.get("threshold", 1.0))
            return JudgeVerdict(
                judge="QwenFallbackJudge",
                approved=merged_score >= threshold,
                confidence=0.5,
                reason=f"Qwen fallback failed, keeping original judgment: {exc}",
                needs_escalation=False,
            )

    def _format_votes(self, votes: list[dict[str, Any]]) -> str:
        """투표 목록을 사람이 읽기 좋은 문자열로 포맷한다.

        Args:
            votes: 모델 투표 결과 목록.

        Returns:
            포맷된 투표 정보 문자열.
        """
        lines = []
        for v in votes:
            lines.append(
                f"- {v.get('model', '?')}: score={v.get('score', 0):.4f}, "
                f"label={v.get('label', '?')}, reason={v.get('reason', 'N/A')}"
            )
        return "\n".join(lines) if lines else "(투표 없음)"
