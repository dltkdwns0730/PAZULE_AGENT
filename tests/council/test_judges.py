import pytest
from app.council.judges import ConsistencyJudge, ThresholdJudge, JudgeContext


class TestConsistencyJudge:
    @pytest.fixture
    def judge(self):
        return ConsistencyJudge()

    def test_all_fields_consistent_pass(self, judge):
        context = JudgeContext(
            mission_type="location",
            ensemble_result={
                "merged_score": 0.8,
                "merged_label": "match",
                "threshold": 0.7,
                "conflict": False,
            },
            model_votes=[{"model": "siglip2", "score": 0.8, "label": "match"}],
            request_context={},
        )
        verdict = judge.evaluate(context)
        assert verdict["approved"] is True
        assert verdict["needs_escalation"] is False
        assert "All fields consistent" in verdict["reason"]

    def test_all_fields_consistent_fail(self, judge):
        context = JudgeContext(
            mission_type="location",
            ensemble_result={
                "merged_score": 0.5,
                "merged_label": "mismatch",
                "threshold": 0.7,
                "conflict": False,
            },
            model_votes=[{"model": "siglip2", "score": 0.5, "label": "mismatch"}],
            request_context={},
        )
        verdict = judge.evaluate(context)
        assert verdict["approved"] is False
        assert verdict["needs_escalation"] is False

    def test_inconsistent_score_high_label_mismatch(self, judge):
        context = JudgeContext(
            mission_type="location",
            ensemble_result={
                "merged_score": 0.8,
                "merged_label": "mismatch",
                "threshold": 0.7,
                "conflict": False,
            },
            model_votes=[],
            request_context={},
        )
        verdict = judge.evaluate(context)
        assert verdict["approved"] is False
        assert verdict["needs_escalation"] is True
        assert "score >= threshold but label is mismatch" in verdict["reason"]

    def test_inconsistent_score_low_label_match(self, judge):
        context = JudgeContext(
            mission_type="location",
            ensemble_result={
                "merged_score": 0.5,
                "merged_label": "match",
                "threshold": 0.7,
                "conflict": False,
            },
            model_votes=[],
            request_context={},
        )
        verdict = judge.evaluate(context)
        assert verdict["approved"] is False
        assert verdict["needs_escalation"] is True
        assert "score < threshold but label is match" in verdict["reason"]

    def test_conflict_escalates(self, judge):
        context = JudgeContext(
            mission_type="location",
            ensemble_result={
                "merged_score": 0.8,
                "merged_label": "match",
                "threshold": 0.7,
                "conflict": True,
            },
            model_votes=[
                {"model": "siglip2", "score": 0.9},
                {"model": "blip", "score": 0.5},
            ],
            request_context={},
        )
        verdict = judge.evaluate(context)
        assert verdict["needs_escalation"] is True
        assert "model conflict detected" in verdict["reason"]


class TestThresholdJudge:
    @pytest.fixture
    def judge(self):
        return ThresholdJudge()

    def test_clear_pass(self, judge):
        context = JudgeContext(
            mission_type="location",
            ensemble_result={"merged_score": 0.9, "threshold": 0.7, "conflict": False},
            model_votes=[],
            request_context={},
        )
        verdict = judge.evaluate(context)
        assert verdict["approved"] is True
        assert verdict["needs_escalation"] is False
        assert "Clear pass" in verdict["reason"]

    def test_clear_fail(self, judge):
        context = JudgeContext(
            mission_type="location",
            ensemble_result={"merged_score": 0.4, "threshold": 0.7, "conflict": False},
            model_votes=[],
            request_context={},
        )
        verdict = judge.evaluate(context)
        assert verdict["approved"] is False
        assert verdict["needs_escalation"] is False
        assert "Clear fail" in verdict["reason"]

    def test_borderline_escalates(self, judge, monkeypatch):
        # margin=0.08, threshold=0.7 -> 0.62 ~ 0.78 is borderline
        context = JudgeContext(
            mission_type="location",
            ensemble_result={"merged_score": 0.75, "threshold": 0.7, "conflict": False},
            model_votes=[],
            request_context={},
        )
        verdict = judge.evaluate(context)
        assert verdict["needs_escalation"] is True
        assert "Borderline score" in verdict["reason"]

    def test_conflict_escalates(self, judge):
        context = JudgeContext(
            mission_type="location",
            ensemble_result={"merged_score": 0.8, "threshold": 0.7, "conflict": True},
            model_votes=[],
            request_context={},
        )
        verdict = judge.evaluate(context)
        assert verdict["needs_escalation"] is True
        assert "Model conflict detected" in verdict["reason"]
