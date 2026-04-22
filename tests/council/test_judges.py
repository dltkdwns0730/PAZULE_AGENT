"""Council Judge 단위 테스트: ConsistencyJudge, ThresholdJudge, QwenFallbackJudge.

공공 환경 호환 설계:
  - 실제 AI 모델 로딩 없음 (ModelRegistry·probe·build_prompt_bundle 모두 mock)
  - 실제 API 키 불필요
  - 각 Judge 클래스를 독립적으로 검증

검증 대상:
  - ConsistencyJudge: 점수/레이블 일관성, 충돌(conflict) 감지, 에스컬레이션 결정
  - ThresholdJudge: 경계값(borderline) 감지, 충돌 감지, clear pass/fail
  - QwenFallbackJudge: 정상 호출 → 승인/거부, 예외 발생 → 앙상블 폴백
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.council.judges import (
    ConsistencyJudge,
    JudgeContext,
    QwenFallbackJudge,
    ThresholdJudge,
)


# ── 헬퍼 ────────────────────────────────────────────────────────────────────


def _make_context(
    merged_score: float = 0.85,
    threshold: float = 0.7,
    merged_label: str = "match",
    conflict: bool = False,
    votes: list[dict[str, Any]] | None = None,
    mission_type: str = "location",
    image_path: str = "fake.jpg",
    answer: str = "target",
) -> JudgeContext:
    if votes is None:
        votes = [
            {"model": "siglip2", "score": merged_score, "label": merged_label},
        ]
    return JudgeContext(
        mission_type=mission_type,
        ensemble_result={
            "merged_score": merged_score,
            "threshold": threshold,
            "merged_label": merged_label,
            "conflict": conflict,
        },
        model_votes=votes,
        request_context={
            "mission_type": mission_type,
            "image_path": image_path,
            "answer": answer,
        },
    )


def _print_judge(judge_name: str, context: JudgeContext, verdict: dict):
    print(f"\n{'=' * 50}")
    print(f"[{judge_name}] EVALUATE")
    print(
        f"  score={context['ensemble_result'].get('merged_score')} "
        f"threshold={context['ensemble_result'].get('threshold')} "
        f"conflict={context['ensemble_result'].get('conflict')}"
    )
    print(
        f"  → approved={verdict['approved']} "
        f"needs_escalation={verdict['needs_escalation']} "
        f"reason={verdict['reason']}"
    )
    print(f"{'=' * 50}\n")


# ── ConsistencyJudge ─────────────────────────────────────────────────────────


class TestConsistencyJudge:
    """ConsistencyJudge.evaluate() 단위 테스트."""

    def test_consistent_pass_returns_approved_true(self) -> None:
        ctx = _make_context(merged_score=0.85, threshold=0.7, merged_label="match")
        verdict = ConsistencyJudge().evaluate(ctx)
        _print_judge("ConsistencyJudge", ctx, verdict)
        assert verdict["approved"] is True

    def test_consistent_pass_no_escalation(self) -> None:
        ctx = _make_context(merged_score=0.85, threshold=0.7, merged_label="match")
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["needs_escalation"] is False

    def test_consistent_pass_high_confidence(self) -> None:
        ctx = _make_context(merged_score=0.85, threshold=0.7, merged_label="match")
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["confidence"] == pytest.approx(0.9)

    def test_consistent_fail_returns_approved_false(self) -> None:
        ctx = _make_context(merged_score=0.5, threshold=0.7, merged_label="mismatch")
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["approved"] is False

    def test_consistent_fail_no_escalation(self) -> None:
        ctx = _make_context(merged_score=0.5, threshold=0.7, merged_label="mismatch")
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["needs_escalation"] is False

    def test_score_above_threshold_but_mismatch_label_escalates(self) -> None:
        """score >= threshold 인데 label=mismatch → 일관성 오류 → 에스컬레이션."""
        ctx = _make_context(merged_score=0.9, threshold=0.7, merged_label="mismatch")
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["needs_escalation"] is True
        assert verdict["approved"] is False

    def test_score_below_threshold_but_match_label_escalates(self) -> None:
        """score < threshold 인데 label=match → 일관성 오류 → 에스컬레이션."""
        ctx = _make_context(merged_score=0.5, threshold=0.7, merged_label="match")
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["needs_escalation"] is True

    def test_no_votes_but_nonzero_score_escalates(self) -> None:
        """투표 없는데 점수 > 0 → 일관성 오류 → 에스컬레이션."""
        ctx = _make_context(
            merged_score=0.8, threshold=0.7, merged_label="match", votes=[]
        )
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["needs_escalation"] is True

    def test_zero_score_no_votes_no_escalation(self) -> None:
        """score=0, votes=[] → 점수도 없고 투표도 없음 → 일관성 이슈 없음."""
        ctx = _make_context(
            merged_score=0.0, threshold=0.7, merged_label="mismatch", votes=[]
        )
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["needs_escalation"] is False

    def test_conflict_flag_triggers_escalation(self) -> None:
        """필드는 일관적이지만 conflict=True → 에스컬레이션."""
        ctx = _make_context(
            merged_score=0.85, threshold=0.7, merged_label="match", conflict=True
        )
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["needs_escalation"] is True

    def test_conflict_flag_confidence_is_moderate(self) -> None:
        ctx = _make_context(
            merged_score=0.85, threshold=0.7, merged_label="match", conflict=True
        )
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["confidence"] == pytest.approx(0.5)

    def test_verdict_judge_name(self) -> None:
        ctx = _make_context()
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["judge"] == "ConsistencyJudge"

    def test_inconsistency_low_confidence(self) -> None:
        ctx = _make_context(merged_score=0.9, threshold=0.7, merged_label="mismatch")
        verdict = ConsistencyJudge().evaluate(ctx)
        assert verdict["confidence"] == pytest.approx(0.3)


# ── ThresholdJudge ───────────────────────────────────────────────────────────


class TestThresholdJudge:
    """ThresholdJudge.evaluate() 단위 테스트."""

    def _evaluate(self, **kwargs) -> dict:
        ctx = _make_context(**kwargs)
        with patch("app.council.judges.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.08
            verdict = ThresholdJudge().evaluate(ctx)
        _print_judge("ThresholdJudge", ctx, verdict)
        return verdict

    def test_clear_pass_approved_true(self) -> None:
        """score=0.9 threshold=0.7 → 명확히 통과, 에스컬레이션 없음."""
        verdict = self._evaluate(merged_score=0.9, threshold=0.7)
        assert verdict["approved"] is True
        assert verdict["needs_escalation"] is False

    def test_clear_fail_approved_false(self) -> None:
        """score=0.4 threshold=0.7 → 명확히 실패, 에스컬레이션 없음."""
        verdict = self._evaluate(merged_score=0.4, threshold=0.7)
        assert verdict["approved"] is False
        assert verdict["needs_escalation"] is False

    def test_clear_pass_high_confidence(self) -> None:
        """distance > margin * 2 이면 confidence=0.95."""
        verdict = self._evaluate(
            merged_score=0.9, threshold=0.7
        )  # distance=0.2, margin*2=0.16
        assert verdict["confidence"] == pytest.approx(0.95)

    def test_moderate_distance_confidence_lower(self) -> None:
        """distance > margin but < margin*2 → confidence=0.8."""
        # margin=0.08, distance=0.12 → 0.08<0.12<0.16
        verdict = self._evaluate(merged_score=0.82, threshold=0.7)
        assert verdict["confidence"] == pytest.approx(0.8)

    def test_borderline_triggers_escalation(self) -> None:
        """distance <= margin(0.08) → 경계값 → 에스컬레이션."""
        verdict = self._evaluate(merged_score=0.75, threshold=0.7)  # distance=0.05
        assert verdict["needs_escalation"] is True

    def test_borderline_approved_reflects_score(self) -> None:
        """경계값에서 approved는 score >= threshold 기준."""
        verdict = self._evaluate(merged_score=0.75, threshold=0.7)
        assert verdict["approved"] is True  # 0.75 >= 0.7

    def test_borderline_below_threshold_approved_false(self) -> None:
        verdict = self._evaluate(merged_score=0.65, threshold=0.7)  # distance=0.05
        assert verdict["approved"] is False

    def test_conflict_triggers_escalation(self) -> None:
        """conflict=True → 무조건 에스컬레이션."""
        verdict = self._evaluate(merged_score=0.9, threshold=0.7, conflict=True)
        assert verdict["needs_escalation"] is True
        assert verdict["approved"] is False

    def test_conflict_confidence_is_low(self) -> None:
        verdict = self._evaluate(merged_score=0.9, threshold=0.7, conflict=True)
        assert verdict["confidence"] == pytest.approx(0.4)

    def test_verdict_judge_name(self) -> None:
        verdict = self._evaluate()
        assert verdict["judge"] == "ThresholdJudge"

    def test_custom_margin_from_settings(self) -> None:
        """settings.COUNCIL_BORDERLINE_MARGIN 값이 실제로 사용되는지 검증."""
        ctx = _make_context(merged_score=0.85, threshold=0.7)  # distance=0.15
        with patch("app.council.judges.settings") as mock_settings:
            # margin=0.2 → distance(0.15) <= 0.2 → borderline
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.2
            verdict = ThresholdJudge().evaluate(ctx)
        assert verdict["needs_escalation"] is True


# ── QwenFallbackJudge ────────────────────────────────────────────────────────


class TestQwenFallbackJudge:
    """QwenFallbackJudge.evaluate() 단위 테스트.

    공공 환경 호환: ModelRegistry·build_prompt_bundle·probe.probe 모두 mock.
    """

    def _make_mock_probe(
        self, score: float = 0.9, reason: str = "looks correct"
    ) -> MagicMock:
        probe = MagicMock()
        probe.probe.return_value = {"score": score, "label": "match", "reason": reason}
        return probe

    def _evaluate_with_mocks(
        self,
        qwen_score: float = 0.9,
        threshold: float = 0.7,
        exception: Exception | None = None,
        merged_score: float = 0.75,
    ) -> dict:
        ctx = _make_context(
            merged_score=merged_score,
            threshold=threshold,
            merged_label="match",
        )
        mock_probe = self._make_mock_probe(score=qwen_score)
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_probe

        if exception:
            mock_probe.probe.side_effect = exception

        # ModelRegistry·build_prompt_bundle은 evaluate() 내부에서 로컬 import됨
        # → 실제 모듈 경로를 패치해야 함
        with (
            patch(
                "app.models.model_registry.ModelRegistry.get_instance",
                return_value=mock_registry,
            ),
            patch(
                "app.models.prompts.build_prompt_bundle",
                return_value={"prompt": "mocked"},
            ),
        ):
            verdict = QwenFallbackJudge().evaluate(ctx)
        _print_judge("QwenFallbackJudge", ctx, verdict)
        return verdict

    def test_qwen_pass_approved_true(self) -> None:
        """Qwen 점수 >= threshold → approved=True."""
        verdict = self._evaluate_with_mocks(qwen_score=0.9, threshold=0.7)
        assert verdict["approved"] is True

    def test_qwen_fail_approved_false(self) -> None:
        """Qwen 점수 < threshold → approved=False."""
        verdict = self._evaluate_with_mocks(qwen_score=0.5, threshold=0.7)
        assert verdict["approved"] is False

    def test_qwen_confidence_equals_score(self) -> None:
        """confidence = qwen_score 값."""
        verdict = self._evaluate_with_mocks(qwen_score=0.88)
        assert verdict["confidence"] == pytest.approx(0.88)

    def test_qwen_no_escalation_after_verdict(self) -> None:
        """Tier 3에서는 항상 needs_escalation=False."""
        verdict = self._evaluate_with_mocks(qwen_score=0.9)
        assert verdict["needs_escalation"] is False

    def test_qwen_verdict_judge_name(self) -> None:
        verdict = self._evaluate_with_mocks()
        assert verdict["judge"] == "QwenFallbackJudge"

    def test_exception_falls_back_to_ensemble_score(self) -> None:
        """Qwen API 예외 → 앙상블 merged_score 기준으로 폴백."""
        verdict = self._evaluate_with_mocks(
            exception=RuntimeError("GPU OOM"),
            merged_score=0.85,
            threshold=0.7,
        )
        assert verdict["approved"] is True  # 0.85 >= 0.7

    def test_exception_fallback_confidence_is_moderate(self) -> None:
        verdict = self._evaluate_with_mocks(
            exception=RuntimeError("timeout"),
            merged_score=0.5,
            threshold=0.7,
        )
        assert verdict["confidence"] == pytest.approx(0.5)

    def test_exception_no_escalation(self) -> None:
        verdict = self._evaluate_with_mocks(exception=ValueError("bad response"))
        assert verdict["needs_escalation"] is False

    def test_exception_reason_mentions_failure(self) -> None:
        verdict = self._evaluate_with_mocks(exception=RuntimeError("crash"))
        assert (
            "fallback" in verdict["reason"].lower()
            or "failed" in verdict["reason"].lower()
        )

    def test_model_registry_called_with_qwen(self) -> None:
        """ModelRegistry.get('qwen') 가 호출되는지 검증."""
        ctx = _make_context()
        mock_probe = self._make_mock_probe()
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_probe

        with (
            patch(
                "app.models.model_registry.ModelRegistry.get_instance",
                return_value=mock_registry,
            ),
            patch(
                "app.models.prompts.build_prompt_bundle",
                return_value={"prompt": "mocked"},
            ),
        ):
            QwenFallbackJudge().evaluate(ctx)

        mock_registry.get.assert_called_once_with("qwen")

    def test_format_votes_empty_list(self) -> None:
        """_format_votes([]) → '(투표 없음)' 반환."""
        judge = QwenFallbackJudge()
        result = judge._format_votes([])
        assert result == "(투표 없음)"

    def test_format_votes_single_vote(self) -> None:
        judge = QwenFallbackJudge()
        votes = [{"model": "siglip2", "score": 0.9, "label": "match", "reason": "ok"}]
        result = judge._format_votes(votes)
        assert "siglip2" in result
        assert "0.9000" in result

    def test_format_votes_multiple_lines(self) -> None:
        judge = QwenFallbackJudge()
        votes = [
            {"model": "siglip2", "score": 0.9, "label": "match", "reason": "ok"},
            {"model": "blip", "score": 0.7, "label": "match", "reason": "good"},
        ]
        lines = judge._format_votes(votes).splitlines()
        assert len(lines) == 2
