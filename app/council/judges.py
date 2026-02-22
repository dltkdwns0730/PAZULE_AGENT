"""Council Judge implementations: Consistency, Threshold, LLMReview."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, TypedDict

from app.core.config import settings


class JudgeContext(TypedDict):
    mission_type: str
    ensemble_result: Dict[str, Any]
    model_votes: List[Dict[str, Any]]
    request_context: Dict[str, Any]


class JudgeVerdict(TypedDict):
    judge: str
    approved: bool
    confidence: float
    reason: str
    needs_escalation: bool


class BaseJudge(ABC):
    @abstractmethod
    def evaluate(self, context: JudgeContext) -> JudgeVerdict:
        ...


class ConsistencyJudge(BaseJudge):
    """Tier 1: 규칙 기반 필드 일관성 검증 (API 호출 없음)."""

    def evaluate(self, context: JudgeContext) -> JudgeVerdict:
        ensemble = context["ensemble_result"]
        votes = context["model_votes"]

        merged_score = float(ensemble.get("merged_score", 0.0))
        merged_label = ensemble.get("merged_label", "mismatch")
        threshold = float(ensemble.get("threshold", 1.0))

        issues: list[str] = []

        # success/label 일관성: score >= threshold인데 label이 mismatch이면 모순
        if merged_score >= threshold and merged_label == "mismatch":
            issues.append("score >= threshold but label is mismatch")
        if merged_score < threshold and merged_label == "match":
            issues.append("score < threshold but label is match")

        # 투표 없이 결과가 있으면 모순
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

        # 명확한 성공 또는 실패
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
        from app.models.model_registry import ModelRegistry
        from app.models.prompts import build_prompt_bundle
        
        ensemble = context["ensemble_result"]
        req = context["request_context"]
        mission_type = req.get("mission_type", "location")
        image_path = req.get("image_path")
        answer = req.get("answer")
        
        try:
            print("\n🚨 [Council] SigLIP2의 1차 판단이 모호하여, Qwen-VL(LLM)을 추가 호출합니다...")
            registry = ModelRegistry.get_instance()
            probe = registry.get("qwen")
            prompt_bundle = build_prompt_bundle(mission_type, answer)
            
            # 무거운 VLM을 이 순간에만 호출함
            qwen_vote = probe.probe(mission_type, image_path, answer, prompt_bundle)
            
            # Qwen 결과를 바탕으로 최종 결론 
            qwen_score = qwen_vote.get("score", 0.0)
            threshold = float(ensemble.get("threshold", 1.0))
            approved = qwen_score >= threshold
            
            print(f"✅ [Council] 추가 모델(Qwen) 판정 완료! Score: {qwen_score:.2f}")

            return JudgeVerdict(
                judge="QwenFallbackJudge",
                approved=approved,
                confidence=qwen_score,
                reason=f"Qwen-VL Fallback Override (Original score was borderline): {qwen_vote.get('reason', '')}",
                needs_escalation=False,
            )
        except Exception as e:
            print(f"[QwenFallbackJudge] Error: {e}")
            # Qwen 통신 실패 시 기존 ensemble(기존 Siglip2) 결과로 안전하게 fallback
            merged_score = float(ensemble.get("merged_score", 0.0))
            threshold = float(ensemble.get("threshold", 1.0))
            return JudgeVerdict(
                judge="QwenFallbackJudge",
                approved=merged_score >= threshold,
                confidence=0.5,
                reason=f"Qwen fallback failed, keeping original judgment: {e}",
                needs_escalation=False,
            )

    def _format_votes(self, votes: List[Dict[str, Any]]) -> str:
        lines = []
        for v in votes:
            lines.append(
                f"- {v.get('model', '?')}: score={v.get('score', 0):.4f}, "
                f"label={v.get('label', '?')}, reason={v.get('reason', 'N/A')}"
            )
        return "\n".join(lines) if lines else "(투표 없음)"

