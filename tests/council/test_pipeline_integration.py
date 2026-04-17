from app.council.graph import pipeline_app


def _print_integration_step(node_name: str, state: dict):
    """테스트 실행 시 터미널에서 전체 파이프라인의 흐름을 시각적으로 확인하기 위한 헬퍼 함수"""
    print(f"\n{'=' * 50}")
    print(f"🔄 [PIPELINE NODE EXECUTED]: {node_name}")
    print(f"{'-' * 50}")

    artifacts = state.get("artifacts", {})
    if node_name == "validator":
        print(f"  - Gate Result: {artifacts.get('gate_result')}")
    elif node_name == "router":
        print(f"  - Route Decision: {state.get('route_decision')}")
    elif node_name == "evaluator":
        print(
            f"  - Model Votes: {len(artifacts.get('model_votes', []))} responses collected."
        )
    elif node_name == "aggregator":
        ensemble = artifacts.get("ensemble_result", {})
        print(
            f"  - Aggregated Score: {ensemble.get('merged_score')} / Threshold: {ensemble.get('threshold')}"
        )
        print(f"  - Conflict: {ensemble.get('conflict')}")
    elif node_name == "council":
        print(f"  - Deliberation: {artifacts.get('council_verdict')}")
    elif node_name == "judge":
        judgment = artifacts.get("judgment", {})
        print(
            f"  - Judgment Success: {judgment.get('success')} (Reason: {judgment.get('reason')})"
        )
    elif node_name == "policy":
        print(f"  - Policy Result: {artifacts.get('coupon_decision')}")
    elif node_name == "responder":
        response = state.get("final_response", {})
        print(f"  - Final UI Theme: {response.get('ui_theme')}")
        print(f"  - Message: {response.get('message')}")
    print(f"{'=' * 50}\n")


class TestPipelineIntegration:
    def test_full_pipeline_success(self, mocker):
        # 1. Mock External Services
        mocker.patch("app.council.nodes.validate_metadata", return_value=True)
        mocker.patch(
            "app.council.nodes.mission_session_service.hash_file",
            return_value="fake_hash_int",
        )
        mocker.patch(
            "app.council.nodes.mission_session_service.is_duplicate_hash_for_user",
            return_value=False,
        )
        # Force validation to be active during test, regardless of .env settings
        mocker.patch("app.council.nodes.settings.SKIP_METADATA_VALIDATION", False)

        # 2. Mock Model Invocations
        mock_invoke = mocker.patch("app.council.nodes._invoke_model")
        mock_invoke.return_value = {
            "model": "mock_model",
            "score": 0.95,
            "label": "match",
        }
        mocker.patch(
            "app.council.nodes.build_prompt_bundle", return_value={"prompt": "mocked"}
        )

        # 3. Initial State
        initial_state = {
            "request_context": {
                "user_id": "integration_user",
                "image_path": "valid_integration_path.jpg",
                "mission_type": "location",
                "answer": "target",
                "model_selection": "ensemble",
            },
            "artifacts": {},
            "errors": [],
            "control_flags": {},
            "messages": [],
        }

        print("\n\n" + "*" * 60)
        print("🚀 STARTING PIPELINE INTEGRATION TEST (SUCCESS PATH)")
        print("*" * 60)

        # 4. Stream Pipeline
        final_state = None
        for s in pipeline_app.stream(initial_state):
            for node_name, state in s.items():
                _print_integration_step(node_name, state)
                final_state = state

        # 5. Final Assertions
        assert final_state is not None
        assert "final_response" in final_state
        assert final_state["final_response"]["ui_theme"] == "confetti"
        assert final_state["final_response"]["data"]["success"] is True

    def test_full_pipeline_gate_blocked(self, mocker):
        # 1. Mock External Services to fail
        mocker.patch("app.council.nodes.validate_metadata", return_value=False)
        mocker.patch(
            "app.council.nodes.mission_session_service.hash_file",
            return_value="fake_hash_int",
        )
        mocker.patch(
            "app.council.nodes.mission_session_service.is_duplicate_hash_for_user",
            return_value=True,
        )
        # Force validation to be active during test, regardless of .env settings
        mocker.patch("app.council.nodes.settings.SKIP_METADATA_VALIDATION", False)

        # 3. Initial State
        initial_state = {
            "request_context": {
                "user_id": "integration_user",
                "image_path": "invalid_integration_path.jpg",
                "mission_type": "location",
            },
            "artifacts": {},
            "errors": [],
            "control_flags": {},
            "messages": [],
        }

        print("\n\n" + "*" * 60)
        print("🚀 STARTING PIPELINE INTEGRATION TEST (GATE BLOCKED PATH)")
        print("*" * 60)

        # 4. Stream Pipeline
        final_state = None
        for s in pipeline_app.stream(initial_state):
            for node_name, state in s.items():
                _print_integration_step(node_name, state)
                final_state = state

        # 5. Final Assertions
        assert final_state is not None
        assert "final_response" in final_state
        assert final_state["final_response"]["ui_theme"] == "error"
        assert final_state["final_response"]["data"]["success"] is False
