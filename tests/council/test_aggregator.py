"""Council aggregator 단위 테스트: tiered_evaluate().

공공 환경 호환 설계:
  - 실제 Qwen 모델 호출 없음 — QwenFallbackJudge 내부 의존성 mock 처리
  - 각 Judge 클래스는 실제 구현 사용 (ConsistencyJudge, ThresholdJudge)
  - QwenFallbackJudge만 ModelRegistry·build_prompt_bundle mock

검증 대상:
  - Tier 1에서 needs_escalation=False → 조기 종료 (tier_reached=1)
  - Tier 2에서 needs_escalation=False → Tier 2에서 종료 (tier_reached=2)
  - Tier 3까지 도달 (tier_reached=3)
  - escalated 플래그 정확성
  - votes 목록에 각 Judge 이름 포함
  - approved/confidence/reason 은 마지막 verdict 기준
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch


from app.council.aggregator import tiered_evaluate
from app.council.judges import JudgeContext


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
        votes = [{"model": "siglip2", "score": merged_score, "label": merged_label}]
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


def _make_qwen_mock(score: float = 0.9) -> tuple[MagicMock, MagicMock]:
    """ModelRegistry + probe mock 쌍 반환."""
    mock_probe = MagicMock()
    mock_probe.probe.return_value = {"score": score, "label": "match", "reason": "ok"}
    mock_registry = MagicMock()
    mock_registry.get.return_value = mock_probe
    return mock_registry, mock_probe


def _evaluate_with_settings(
    context: JudgeContext, borderline_margin: float = 0.08
) -> dict:
    """settings.COUNCIL_BORDERLINE_MARGIN을 mock하여 tiered_evaluate 실행."""
    with patch("app.council.judges.settings") as mock_settings:
        mock_settings.COUNCIL_BORDERLINE_MARGIN = borderline_margin
        return tiered_evaluate(context)


def _evaluate_with_qwen_mock(
    context: JudgeContext,
    qwen_score: float = 0.9,
    borderline_margin: float = 0.08,
) -> dict:
    """ThresholdJudge·QwenFallbackJudge 모두 mock 필요한 경우.

    ModelRegistry·build_prompt_bundle은 evaluate() 내부 로컬 import →
    실제 모듈 경로를 패치해야 함.
    """
    mock_registry, _ = _make_qwen_mock(score=qwen_score)
    with (
        patch("app.council.judges.settings") as mock_settings,
        patch(
            "app.models.model_registry.ModelRegistry.get_instance",
            return_value=mock_registry,
        ),
        patch(
            "app.models.prompts.build_prompt_bundle",
            return_value={"prompt": "mocked"},
        ),
    ):
        mock_settings.COUNCIL_BORDERLINE_MARGIN = borderline_margin
        return tiered_evaluate(context)


# ── 조기 종료 (Tier 1) ──────────────────────────────────────────────────────


class TestTieredEvaluateEarlyExitTier1:
    """ConsistencyJudge에서 needs_escalation=False → Tier 1 조기 종료."""

    def test_clear_pass_tier_reached_1(self) -> None:
        ctx = _make_context(
            merged_score=0.85, threshold=0.7, merged_label="match", conflict=False
        )
        result = _evaluate_with_settings(ctx)
        print(
            f"\n[tiered_evaluate] tier_reached={result['tier_reached']} approved={result['approved']}"
        )
        assert result["tier_reached"] == 1

    def test_clear_pass_not_escalated(self) -> None:
        ctx = _make_context(merged_score=0.85, threshold=0.7, merged_label="match")
        result = _evaluate_with_settings(ctx)
        assert result["escalated"] is False

    def test_clear_pass_approved_true(self) -> None:
        ctx = _make_context(merged_score=0.85, threshold=0.7, merged_label="match")
        result = _evaluate_with_settings(ctx)
        assert result["approved"] is True

    def test_clear_fail_tier_reached_1(self) -> None:
        """consistent fail 도 Tier 1에서 종료."""
        ctx = _make_context(merged_score=0.5, threshold=0.7, merged_label="mismatch")
        result = _evaluate_with_settings(ctx)
        assert result["tier_reached"] == 1
        assert result["approved"] is False

    def test_votes_list_contains_consistency_judge(self) -> None:
        ctx = _make_context(merged_score=0.85, threshold=0.7, merged_label="match")
        result = _evaluate_with_settings(ctx)
        assert result["votes"][0]["judge"] == "ConsistencyJudge"


# ── Tier 2 종료 ─────────────────────────────────────────────────────────────


class TestTieredEvaluateExitAtTier2:
    """ConsistencyJudge에서 에스컬레이션 → ThresholdJudge에서 종료."""

    def test_conflict_with_clear_score_stops_at_tier2(self) -> None:
        """conflict=True → ConsistencyJudge 에스컬레이션 → ThresholdJudge conflict → 에스컬레이션
        BUT ThresholdJudge needs_escalation=True → Tier 3 호출 발생.
        Tier 2에서 멈추려면: conflict=False이지만 inconsistency가 있고, ThresholdJudge는 명확한 패스."""
        # score >= threshold이지만 label=mismatch → ConsistencyJudge 에스컬레이션
        # ThresholdJudge에서 score=0.9, threshold=0.7 → distance=0.2 >> margin=0.08 → clear pass, 에스컬레이션 없음
        ctx = _make_context(
            merged_score=0.9,
            threshold=0.7,
            merged_label="mismatch",  # inconsistency!
            conflict=False,
        )
        result = _evaluate_with_settings(ctx, borderline_margin=0.08)
        print(f"\n[tiered_evaluate] tier_reached={result['tier_reached']}")
        assert result["tier_reached"] == 2

    def test_tier2_exit_is_escalated_true(self) -> None:
        ctx = _make_context(
            merged_score=0.9, threshold=0.7, merged_label="mismatch", conflict=False
        )
        result = _evaluate_with_settings(ctx, borderline_margin=0.08)
        assert result["escalated"] is True

    def test_tier2_votes_has_two_judges(self) -> None:
        ctx = _make_context(
            merged_score=0.9, threshold=0.7, merged_label="mismatch", conflict=False
        )
        result = _evaluate_with_settings(ctx, borderline_margin=0.08)
        assert len(result["votes"]) == 2
        judge_names = {v["judge"] for v in result["votes"]}
        assert "ConsistencyJudge" in judge_names
        assert "ThresholdJudge" in judge_names


# ── Tier 3 도달 ─────────────────────────────────────────────────────────────


class TestTieredEvaluateReachesTier3:
    """Tier 3(QwenFallbackJudge)까지 도달하는 시나리오."""

    def test_conflict_reaches_tier3(self) -> None:
        """conflict=True → ConsistencyJudge 에스컬레이션 → ThresholdJudge conflict → 에스컬레이션 → Tier 3."""
        ctx = _make_context(
            merged_score=0.85, threshold=0.7, merged_label="match", conflict=True
        )
        result = _evaluate_with_qwen_mock(ctx, qwen_score=0.9)
        print(f"\n[tiered_evaluate] tier_reached={result['tier_reached']}")
        assert result["tier_reached"] == 3

    def test_borderline_reaches_tier3(self) -> None:
        """borderline score → ThresholdJudge 에스컬레이션 → Tier 3."""
        # ConsistencyJudge: consistent → 에스컬레이션 없음???
        # 아니다 — conflict=False, consistent → needs_escalation=False → Tier 1에서 끝남
        # Tier 3에 도달하려면: ConsistencyJudge 에스컬레이션 + ThresholdJudge 에스컬레이션 필요
        # ConsistencyJudge 에스컬레이션 조건: inconsistency 또는 conflict
        # conflict=False + borderline score + consistent label → ConsistencyJudge stops at Tier 1
        # So: conflict=True forces ConsistencyJudge to escalate AND ThresholdJudge to escalate
        ctx = _make_context(
            merged_score=0.75, threshold=0.7, merged_label="match", conflict=True
        )
        result = _evaluate_with_qwen_mock(ctx, qwen_score=0.8, borderline_margin=0.08)
        assert result["tier_reached"] == 3

    def test_tier3_votes_has_three_judges(self) -> None:
        ctx = _make_context(
            merged_score=0.85, threshold=0.7, merged_label="match", conflict=True
        )
        result = _evaluate_with_qwen_mock(ctx, qwen_score=0.9)
        assert len(result["votes"]) == 3
        judge_names = {v["judge"] for v in result["votes"]}
        assert "QwenFallbackJudge" in judge_names

    def test_tier3_approved_reflects_qwen_score(self) -> None:
        """Tier 3 approved는 Qwen 점수 기준."""
        ctx = _make_context(
            merged_score=0.85, threshold=0.7, merged_label="match", conflict=True
        )
        result = _evaluate_with_qwen_mock(ctx, qwen_score=0.9, borderline_margin=0.08)
        assert result["approved"] is True

    def test_tier3_qwen_fail_approved_false(self) -> None:
        ctx = _make_context(
            merged_score=0.85, threshold=0.7, merged_label="match", conflict=True
        )
        result = _evaluate_with_qwen_mock(ctx, qwen_score=0.5, borderline_margin=0.08)
        assert result["approved"] is False

    def test_tier3_escalated_true(self) -> None:
        ctx = _make_context(
            merged_score=0.85, threshold=0.7, merged_label="match", conflict=True
        )
        result = _evaluate_with_qwen_mock(ctx, qwen_score=0.9)
        assert result["escalated"] is True


# ── 결과 구조 검증 ────────────────────────────────────────────────────────────


class TestTieredEvaluateReturnStructure:
    """tiered_evaluate() 반환값 구조 검증."""

    def test_result_has_approved_key(self) -> None:
        ctx = _make_context()
        result = _evaluate_with_settings(ctx)
        assert "approved" in result

    def test_result_has_confidence_key(self) -> None:
        ctx = _make_context()
        result = _evaluate_with_settings(ctx)
        assert "confidence" in result

    def test_result_has_reason_key(self) -> None:
        ctx = _make_context()
        result = _evaluate_with_settings(ctx)
        assert "reason" in result

    def test_result_has_escalated_key(self) -> None:
        ctx = _make_context()
        result = _evaluate_with_settings(ctx)
        assert "escalated" in result

    def test_result_has_tier_reached_key(self) -> None:
        ctx = _make_context()
        result = _evaluate_with_settings(ctx)
        assert "tier_reached" in result

    def test_result_has_votes_key(self) -> None:
        ctx = _make_context()
        result = _evaluate_with_settings(ctx)
        assert "votes" in result

    def test_votes_items_have_judge_approved_reason(self) -> None:
        ctx = _make_context()
        result = _evaluate_with_settings(ctx)
        for vote in result["votes"]:
            assert "judge" in vote
            assert "approved" in vote
            assert "reason" in vote
