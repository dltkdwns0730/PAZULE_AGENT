import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
from app.council.graph import pipeline_app
from app.services.answer_service import get_today_answers
from app.services.mission_session_service import mission_session_service
import traceback


def run_test_pipeline():
    try:
        # 1. Setup mock session variables
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = r"c:\Users\irubw\geminiProject\projects\active\PAZULE\data\assets\피노지움 조각상\1659956580134.jpg"

        # fallback: if image doesn't exist, create a mock one
        if not os.path.exists(image_path):
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            try:
                from PIL import Image

                test_img = Image.new("RGB", (640, 480), (100, 150, 200))
                test_img.save(image_path)
            except ImportError:
                # If PIL is not available, try other assets
                assets = os.listdir(os.path.join(project_root, "docs", "assets"))
                if assets:
                    image_path = os.path.join(project_root, "docs", "assets", assets[0])
        user_id = "test-user"
        site_id = "test-site"
        mission_type = "location"

        # We need an answer for location
        a1, a2, h1, h2 = get_today_answers()
        answer = a1  # target location answer (피노지움 조각상)
        hint = h1

        # Override for exact match in this test if needed
        answer = "피노지움 조각상"

        print("--- INIT ---")
        print(f"Target Answer: {answer}")
        print(f"Image: {image_path}")
        print(f"Mission: {mission_type}")
        print("-------------")

        # Create session so we can pass mission_id
        session = mission_session_service.create_session(
            user_id=user_id,
            site_id=site_id,
            mission_type=mission_type,
            answer=answer,
            hint=hint,
        )
        mission_id = session["mission_id"]

        # 1. Pipeline Input Configuration
        initial_state = {
            "request_context": {
                "user_id": "tester_01",
                "mission_type": "location",
                "answer": "피노지움 조각상",
                "image_path": r"c:\Users\irubw\geminiProject\projects\active\PAZULE\data\assets\피노지움 조각상\1659956580134.jpg",
                "mission_id": mission_id,
                "site_id": site_id,
                "model_selection": "ensemble",  # use ensemble for full trace
            },
            "artifacts": {},
            "errors": [],
            "control_flags": {},
            "messages": [],
        }

        # 2. Stream through LangGraph
        print("\nStreaming Pipeline Execution:\n")

        # stream yields (node_name, state_output)
        for s in pipeline_app.stream(initial_state):
            for node_name, state in s.items():
                print(f"\n[NODE COMPLETED]: {node_name}")
                artifacts = state.get("artifacts", {})

                if node_name == "validator":
                    print(f" - Gate Result: {artifacts.get('gate_result')}")
                elif node_name == "router":
                    # router returns route_decision at top level of its output dict
                    print(f" - Route Decision: {state.get('route_decision')}")
                elif node_name == "evaluator":
                    print(" - Model Votes:")
                    for idx, vote in enumerate(artifacts.get("model_votes", [])):
                        print(
                            f"    [{idx}] Model: {vote.get('model', 'N/A')}, Score: {vote.get('score', 0):.2f}, Label: {vote.get('label', '')}"
                        )
                elif node_name == "aggregator":
                    ens = artifacts.get("ensemble_result", {})
                    print(f" - Aggregated Score: {ens.get('merged_score')}")
                    print(f" - Threshold: {ens.get('threshold')}")
                    print(f" - Conflict: {ens.get('conflict')}")
                elif node_name == "council":
                    print(f" - Council Verdict: {artifacts.get('council_verdict')}")
                elif node_name == "judge":
                    print(f" - Judgment: {artifacts.get('judgment')}")
                elif node_name == "policy":
                    print(f" - Policy Result: {artifacts.get('coupon_decision')}")
                elif node_name == "responder":
                    print(
                        f" - Final Response Data: {state.get('final_response', {}).get('data')}"
                    )

    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    from app.models.model_registry import register_default_models
    from app.prompts.registry import PromptRegistry
    from app.core.config import settings

    PromptRegistry.get_instance().load_all(settings.PROMPT_TEMPLATES_DIR)
    register_default_models()

    # Needs async event loop patching for some model requests possibly, but we trust LangGraph is sync enough
    run_test_pipeline()
