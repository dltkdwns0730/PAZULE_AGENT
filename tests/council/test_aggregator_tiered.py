import pytest
from unittest.mock import patch
from app.council.aggregator import tiered_evaluate
from app.council.judges import JudgeVerdict


class TestTieredEvaluate:
    """tiered_evaluate 함수(Tier 1 -> 2 -> 3 순차 실행) 검증."""

    @pytest.fixture
    def mock_context(self):
        return {
            "mission_type": "location",
            "ensemble_result": {
                "merged_score": 0.8,
                "threshold": 0.7,
                "conflict": False,
            },
            "model_votes": [],
            "request_context": {},
        }

    def test_stop_at_tier_1_when_consistent(self, mock_context):
        """일관성이 확인되면 Tier 1에서 종료한다."""
        with patch("app.council.judges.ConsistencyJudge.evaluate") as mock_c:
            mock_c.return_value = JudgeVerdict(
                judge="ConsistencyJudge",
                approved=True,
                confidence=0.9,
                reason="OK",
                needs_escalation=False,
            )

            result = tiered_evaluate(mock_context)

            assert result["tier_reached"] == 1
            assert result["escalated"] is False
            assert result["approved"] is True

    def test_escalate_to_tier_2(self, mock_context):
        """Tier 1에서 에스컬레이션이 필요하면 Tier 2까지 진행한다."""
        with patch("app.council.judges.ConsistencyJudge.evaluate") as mock_c, patch(
            "app.council.judges.ThresholdJudge.evaluate"
        ) as mock_t:
            mock_c.return_value = JudgeVerdict(
                judge="ConsistencyJudge",
                approved=True,
                confidence=0.5,
                reason="Conflict",
                needs_escalation=True,
            )
            mock_t.return_value = JudgeVerdict(
                judge="ThresholdJudge",
                approved=True,
                confidence=0.9,
                reason="OK",
                needs_escalation=False,
            )

            result = tiered_evaluate(mock_context)

            assert result["tier_reached"] == 2
            assert result["escalated"] is True
            assert result["approved"] is True

    def test_escalate_to_tier_3(self, mock_context):
        """Tier 2에서도 에스컬레이션이 필요하면 Tier 3(Qwen)까지 진행한다."""
        with patch("app.council.judges.ConsistencyJudge.evaluate") as mock_c, patch(
            "app.council.judges.ThresholdJudge.evaluate"
        ) as mock_t, patch("app.council.judges.QwenFallbackJudge.evaluate") as mock_q:
            mock_c.return_value = JudgeVerdict(
                judge="C",
                approved=True,
                confidence=0.5,
                reason="R",
                needs_escalation=True,
            )
            mock_t.return_value = JudgeVerdict(
                judge="T",
                approved=True,
                confidence=0.5,
                reason="R",
                needs_escalation=True,
            )
            mock_q.return_value = JudgeVerdict(
                judge="Q",
                approved=False,
                confidence=0.1,
                reason="Qwen Says No",
                needs_escalation=False,
            )

            result = tiered_evaluate(mock_context)

            assert result["tier_reached"] == 3
            assert result["escalated"] is True
            assert result["approved"] is False
            assert "Qwen Says No" in result["reason"]
