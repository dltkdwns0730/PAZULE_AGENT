import pytest
from unittest.mock import patch
from app.council.deliberation import council
from app.core.config import settings


class TestCouncilNode:
    """deliberation.py의 council 노드 함수 검증."""

    @pytest.fixture
    def mock_state(self):
        return {
            "request_context": {"mission_type": "location"},
            "artifacts": {
                "ensemble_result": {"merged_score": 0.8, "threshold": 0.7},
                "model_votes": [],
            },
            "messages": [],
        }

    def test_council_disabled_passthrough(self, mock_state, monkeypatch):
        """COUNCIL_ENABLED=False이면 tiered_evaluate를 호출하지 않고 패스스루한다."""
        monkeypatch.setattr(settings, "COUNCIL_ENABLED", False)

        with patch("app.council.deliberation.tiered_evaluate") as mock_eval:
            result = council(mock_state)

            assert mock_eval.call_count == 0
            assert "council_verdict" not in result["artifacts"]
            assert "council: disabled" in result["messages"][0]

    def test_council_enabled_executes_evaluate(self, mock_state, monkeypatch):
        """COUNCIL_ENABLED=True이면 tiered_evaluate를 호출하고 결과를 저장한다."""
        monkeypatch.setattr(settings, "COUNCIL_ENABLED", True)

        mock_verdict = {
            "approved": True,
            "confidence": 0.9,
            "reason": "OK",
            "tier_reached": 1,
            "escalated": False,
        }

        with patch(
            "app.council.deliberation.tiered_evaluate", return_value=mock_verdict
        ):
            result = council(mock_state)

            assert result["artifacts"]["council_verdict"] == mock_verdict
            assert "council: tier=1, approved=True" in result["messages"][0]
