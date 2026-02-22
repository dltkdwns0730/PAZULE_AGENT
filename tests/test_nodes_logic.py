import unittest

from app.council.nodes import coupon_policy_engine, decision_engine, evidence_aggregator, task_router


class NodesLogicTest(unittest.TestCase):
    def test_task_router_normalizes_photo_to_atmosphere(self):
        state = {"request_context": {"mission_type": "photo"}}
        out = task_router(state)
        self.assertEqual(out["request_context"]["mission_type"], "atmosphere")

    def test_aggregator_creates_merged_score(self):
        state = {
            "request_context": {"mission_type": "location"},
            "artifacts": {
                "model_votes": [
                    {"model": "blip", "label": "match", "score": 0.9},
                    {"model": "qwen", "label": "match", "score": 0.8},
                    {"model": "clip", "label": "mismatch", "score": 0.3},
                ]
            },
        }
        out = evidence_aggregator(state)
        merged = out["artifacts"]["ensemble_result"]["merged_score"]
        self.assertGreater(merged, 0.0)
        self.assertLessEqual(merged, 1.0)

    def test_decision_engine_marks_fail_under_threshold(self):
        state = {
            "artifacts": {
                "gate_result": {"passed": True},
                "ensemble_result": {
                    "mission_type": "location",
                    "merged_score": 0.2,
                    "threshold": 0.7,
                    "conflict": False,
                },
            },
            "errors": [],
            "control_flags": {},
        }
        out = decision_engine(state)
        self.assertFalse(out["artifacts"]["judgment"]["success"])

    def test_coupon_policy_checks_success(self):
        state = {
            "artifacts": {
                "gate_result": {"risk_flags": []},
                "judgment": {"success": True},
            }
        }
        out = coupon_policy_engine(state)
        self.assertTrue(out["artifacts"]["coupon_decision"]["eligible"])


if __name__ == "__main__":
    unittest.main()
