import pytest
from typing import Any, Dict

from app.council.nodes import (
    validator,
    router,
    evaluator,
    aggregator,
    judge,
    policy,
    responder,
)


def _print_io(node_name: str, input_state: Dict[str, Any], output_state: Dict[str, Any]):
    """테스트 실행 시 터미널에서 입출력을 시각적으로 확인하기 위한 헬퍼 함수"""
    print(f"\n{'='*50}")
    print(f"[{node_name}] MODULE EXECUTION")
    print(f"{'-'*50}")
    print(f"▶ INPUT STATE:")
    for k, v in input_state.items():
        if v:
            print(f"  - {k}: {v}")
    print(f"◀ OUTPUT STATE:")
    for k, v in output_state.items():
        if v:
            print(f"  - {k}: {v}")
    print(f"{'='*50}\n")


class TestGateKeeper:
    def test_validator_missing_image(self):
        input_state = {
            "request_context": {"user_id": "test_user"},
            "artifacts": {},
            "errors": [],
            "control_flags": {},
        }
        
        output = validator(input_state)
        _print_io("validator (missing image)", input_state, output)
        
        gate_result = output["artifacts"]["gate_result"]
        assert gate_result["passed"] is False
        assert output["control_flags"]["terminate"] is True
        assert output["errors"][0]["code"] == "MISSING_IMAGE"

    def test_validator_success(self, mocker):
        mocker.patch("app.council.nodes.validate_metadata", return_value=True)
        mocker.patch("app.council.nodes.mission_session_service.hash_file", return_value="fake_hash")
        mocker.patch("app.council.nodes.mission_session_service.is_duplicate_hash_for_user", return_value=False)

        input_state = {
            "request_context": {"user_id": "test_user", "image_path": "valid/path.jpg"},
            "artifacts": {},
            "errors": [],
            "control_flags": {},
        }
        
        output = validator(input_state)
        _print_io("validator (success)", input_state, output)
        
        gate_result = output["artifacts"]["gate_result"]
        assert gate_result["passed"] is True
        assert gate_result["metadata_valid"] is True
        assert gate_result["is_duplicate"] is False
        assert "terminate" not in output["control_flags"]


class TestTaskRouter:
    def test_router_photo_to_atmosphere(self):
        input_state = {
            "request_context": {"mission_type": "photo"}
        }
        output = router(input_state)
        _print_io("router (photo -> atmosphere)", input_state, output)
        
        assert output["request_context"]["mission_type"] == "atmosphere"
        assert output["route_decision"]["next_node"] == "evaluator"


class TestModelFanout:
    def test_evaluator_atmosphere(self, mocker):
        mock_invoke = mocker.patch("app.council.nodes._invoke_model")
        mock_invoke.return_value = {"model": "siglip2", "score": 0.85, "label": "match"}
        
        mocker.patch("app.council.nodes.build_prompt_bundle", return_value={"prompt": "mocked"})
        
        input_state = {
            "request_context": {
                "mission_type": "atmosphere",
                "image_path": "fake.jpg",
                "answer": "sunset",
                "model_selection": "siglip2"
            },
            "artifacts": {},
            "errors": []
        }
        
        output = evaluator(input_state)
        _print_io("evaluator (atmosphere, siglip2)", input_state, output)
        
        assert len(output["artifacts"]["model_votes"]) == 1
        assert output["artifacts"]["model_votes"][0]["score"] == 0.85


class TestEvidenceAggregator:
    def test_aggregator_location(self):
        input_state = {
            "request_context": {"mission_type": "location"},
            "artifacts": {
                "model_votes": [
                    {"model": "blip", "score": 0.9, "label": "match"},
                    {"model": "qwen", "score": 0.8, "label": "match"}
                ]
            }
        }
        
        output = aggregator(input_state)
        _print_io("aggregator (location pass)", input_state, output)
        
        ensemble = output["artifacts"]["ensemble_result"]
        # blip(0.45) * 0.9 + qwen(0.35) * 0.8 = 0.405 + 0.280 = 0.685
        # Total weight = 0.45 + 0.35 = 0.8
        # Merged = 0.685 / 0.8 = 0.85625 ≈ 0.8562
        assert ensemble["merged_score"] > 0.8
        assert ensemble["merged_label"] == "match"
        assert ensemble["conflict"] is False


class TestDecisionEngine:
    def test_judge_success(self):
        input_state = {
            "artifacts": {
                "gate_result": {"passed": True},
                "ensemble_result": {
                    "mission_type": "location",
                    "merged_score": 0.85,
                    "threshold": 0.7,
                    "conflict": False
                }
            },
            "control_flags": {},
            "errors": []
        }
        
        output = judge(input_state)
        _print_io("judge (success)", input_state, output)
        
        judgment = output["artifacts"]["judgment"]
        assert judgment["success"] is True
        assert judgment["reason"] == "score_passed"


class TestCouponPolicyEngine:
    def test_policy_eligible(self):
        input_state = {
            "artifacts": {
                "judgment": {"success": True},
                "gate_result": {"risk_flags": []}
            }
        }
        
        output = policy(input_state)
        _print_io("policy (eligible)", input_state, output)
        
        assert output["artifacts"]["coupon_decision"]["eligible"] is True


class TestFinalizer:
    def test_responder_success(self):
        input_state = {
            "request_context": {"mission_type": "location"},
            "artifacts": {
                "gate_result": {"passed": True},
                "judgment": {"success": True, "confidence": 0.85},
                "coupon_decision": {"eligible": True},
                "model_votes": []
            },
            "errors": []
        }
        
        output = responder(input_state)
        _print_io("responder (success)", input_state, output)
        
        response = output["final_response"]
        assert response["ui_theme"] == "confetti"
        assert response["data"]["success"] is True
        assert response["data"]["couponEligible"] is True
