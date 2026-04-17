import os
import sys
import logging

# 1. Path Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.council.deliberation import council
from app.models.model_registry import register_default_models
from app.prompts.registry import PromptRegistry
from app.core.config import settings

# Logging Setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def run_council_verification():
    """Council(Qwen-VL) 노드만을 집중적으로 검증하기 위한 테스트 스크립트."""
    try:
        print("\n" + "=" * 50)
        print("COUNCIL (QWEN-VL) INDEPENDENT VERIFICATION")
        print("=" * 50)

        # 1. 초기 상태 설정 (강제 에스컬레이션 모사)
        # 상황: SigLIP2는 mismatch(0.40)라고 하고, BLIP은 match(1.0)라고 하여 충돌이 발생한 경우
        mission_type = "location"
        answer = "피노지움 조각상"
        image_path = r"c:\Users\irubw\geminiProject\projects\active\PAZULE\data\assets\피노지움 조각상\1659956580134.jpg"

        if not os.path.exists(image_path):
            print(f"Error: Image not found at {image_path}")
            return

        # 앙상블 결과 모의 객체
        mock_ensemble_result = {
            "mission_type": mission_type,
            "merged_score": 0.68,  # 임계점(0.7)에 살짝 미달하는 경계값
            "merged_label": "mismatch",
            "threshold": 0.7,
            "conflict": True,  # 모델 간 이견 발생 강제 설정
            "vote_count": 2,
        }

        # 개별 모델 투표 결과 모의 객체
        mock_model_votes = [
            {
                "model": "siglip2",
                "score": 0.40,
                "label": "mismatch",
                "reason": "SigLIP2 low confidence match",
            },
            {
                "model": "blip",
                "score": 1.00,
                "label": "match",
                "reason": "BLIP VQA exact keyword found",
            },
        ]

        # PipelineState 구성
        mock_state = {
            "request_context": {
                "mission_type": mission_type,
                "answer": answer,
                "image_path": image_path,
                "user_id": "council_tester",
            },
            "artifacts": {
                "ensemble_result": mock_ensemble_result,
                "model_votes": mock_model_votes,
            },
            "messages": [],
        }

        print(f"\n[Scenario] Mission: {mission_type}, Answer: {answer}")
        print(
            f"[Scenario] Ensemble Score: {mock_ensemble_result['merged_score']} (Threshold: 0.7)"
        )
        print(f"[Scenario] Conflict Status: {mock_ensemble_result['conflict']}")
        print("-" * 30)

        # 2. Council 노드 직접 실행
        print("\n>>> Council 노드 실행 (Qwen-VL 호출 시뮬레이션)...")
        output = council(mock_state)

        # 3. 결과 출력
        verdict = output.get("artifacts", {}).get("council_verdict", {})

        print("\n" + "*" * 50)
        print("COUNCIL FINAL VERDICT REPORT")
        print("*" * 50)
        if verdict:
            print(
                f" - Result: {'APPROVED ✅' if verdict.get('approved') else 'FAILED ❌'}"
            )
            print(f" - Tier Reached: {verdict.get('tier_reached')}")
            print(f" - Reason: {verdict.get('reason')}")
            print(f" - Confidence: {verdict.get('confidence')}")

            print("\n[Judge Breakdown]")
            for i, v in enumerate(verdict.get("votes", [])):
                print(
                    f"   Tier {i + 1} ({v.get('judge')}): Approved={v.get('approved')}, Reason: {v.get('reason')}"
                )
        else:
            print("Error: Council produced no verdict.")
        print("*" * 50)

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 필수 레지스트리 로드
    PromptRegistry.get_instance().load_all(settings.PROMPT_TEMPLATES_DIR)
    register_default_models()

    run_council_verification()
