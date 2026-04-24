import os
import argparse
import logging
from app.core.config import settings
from app.models.model_registry import register_default_models, ModelRegistry
from app.models.prompts import build_prompt_bundle

# 로그 레벨 조정 (상세 로그 억제)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("SimpleTest")

# 기본 에셋 경로 설정
ASSETS_BASE = r"C:\Users\irubw\geminiProject\projects\active\PAZULE\data\assets"


def test_single_image(image_path, target_atmosphere):
    # 입력된 경로가 존재하지 않으면 기본 에셋 경로에서 찾음
    if not os.path.exists(image_path):
        candidate_path = os.path.join(ASSETS_BASE, image_path)
        if os.path.exists(candidate_path):
            image_path = candidate_path
        else:
            print("Error: 파일을 찾을 수 없습니다.")
            print(f"  - 입력된 경로: {image_path}")
            print(f"  - 에셋 기준 경로: {candidate_path}")
            return

    # 1. 모델 등록 및 초기화
    register_default_models()
    registry = ModelRegistry.get_instance()

    # 2. 프롬프트 생성
    prompt_bundle = build_prompt_bundle("atmosphere", target_atmosphere)

    print("\n" + "=" * 50)
    print(" 📸 이미지 분석 테스트")
    print(f"  - 경로: {image_path}")
    print(f"  - 목표 분위기: [{target_atmosphere}]")
    print("=" * 50)

    # 3. 모델별 실행 및 점수 출력
    models = ["siglip2", "blip"]

    results = {}
    for model_name in models:
        try:
            print(f" ⏳ {model_name} 분석 중...", end="\r")
            probe = registry.get(model_name)
            res = probe.probe(
                "atmosphere", image_path, target_atmosphere, prompt_bundle
            )
            results[model_name] = res
        except Exception as e:
            results[model_name] = {"score": 0.0, "error": str(e)}

    print(" " * 30, end="\r")  # 청소

    for name, data in results.items():
        score = data.get("score", 0.0)
        label = data.get("label", "N/A")
        status = "✅ PASS" if label == "match" else "❌ FAIL"

        print(f" [{name.upper()}]")
        print(f"  - Score: {score:.4f}")
        print(f"  - Label: {label} ({status})")

        # BLIP인 경우 상세 답변(Visual Context) 출력
        if name == "blip":
            from app.models.blip import get_visual_context

            context = get_visual_context(image_path)
            print("  - [BLIP 상세 분석 내용]")
            for line in context.split("\n"):
                print(f"    {line}")

        if "error" in data:
            print(f"  - Error: {data['error']}")
        print("-" * 30)

    # 가중치 계산 (실제 서비스 로직과 동일하게)
    from app.core.config import constants

    weights = constants.ATMOSPHERE_MODEL_WEIGHTS

    weighted_sum = 0.0
    total_weight = 0.0
    for name, data in results.items():
        w = weights.get(name, 1.0)
        weighted_sum += data.get("score", 0.0) * w
        total_weight += w

    final_score = weighted_sum / total_weight
    threshold = settings.ATMOSPHERE_PASS_THRESHOLD

    print("\n [최종 병합 결과]")
    print(f"  - Merged Score: {final_score:.4f}")
    print(f"  - Threshold: {threshold}")
    print(f"  - 최종 판정: {'🎉 성공' if final_score >= threshold else '🔒 실패'}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PAZULE 분위기 미션 점수 측정 도구")
    parser.add_argument("image", help="분석할 이미지 파일의 경로")
    parser.add_argument(
        "--mood", default="화사한", help="테스트할 분위기 키워드 (기본값: 화사한)"
    )

    args = parser.parse_args()

    test_single_image(args.image, args.mood)
