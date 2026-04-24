import os
from app.models.model_registry import register_default_models
from app.council.nodes import evaluator, aggregator, judge, responder
from app.core.config import settings


def simulate():
    register_default_models()
    # 테스트를 위해 임계값 설정 확인
    settings.ATMOSPHERE_PASS_THRESHOLD = 0.5

    test_cases = [
        {
            "name": "1. 성공 케이스 (나남출판사 -> 자연적인)",
            "img": "data/assets/나남출판사/nanam_06.jpg",
            "target": "차분하고 자연적인",
        },
        {
            "name": "2. 실패 케이스 (부엉이 -> 화사한 / 대비 힌트 테스트)",
            "img": "data/assets/로드킬부엉이/owl_01.jpg",
            "target": "화사하고 활기찬",
        },
        {
            "name": "3. 무효 케이스 (단색 이미지 -> 필터링 테스트)",
            "img": "data/assets/창틀피노키오/pino_window_01.jpg",
            "target": "동화적이고 장난스러운",
        },
    ]

    for case in test_cases:
        print(f"\n{'=' * 60}")
        print(f"Scenario: {case['name']}")
        print(f"{'=' * 60}")

        # 실제 경로 확인 (한글/영어 혼용 대응)
        img_path = case["img"]
        if not os.path.exists(img_path):
            # 폴더명 공백 제거 등 재시도
            img_path = img_path.replace(" ", "")

        # 파이프라인 State 모사
        state = {
            "request_context": {
                "mission_type": "atmosphere",
                "image_path": img_path,
                "answer": case["target"],
                "static_hint": "사진을 다시 찍어보세요.",
            },
            "artifacts": {
                "gate_result": {
                    "passed": True
                }  # 이미지 유효성 검사는 파이프라인 내부 로직으로 시뮬레이션
            },
            "errors": [],
            "control_flags": {},
        }

        # 1. Evaluator (모델 실행)
        state.update(evaluator(state))

        # 2. Aggregator (점수 합계)
        state.update(aggregator(state))

        # 3. Judge (합격 판정)
        state.update(judge(state))

        # 4. Responder (응답 및 힌트 생성)
        result = responder(state)

        final = result["final_response"]
        print(f"결과: {final['ui_theme'].upper()}")
        print(f"메시지: {final['message']}")
        if "hint" in final["data"]:
            print(f"제공된 힌트: {final['data']['hint']}")
        print(f"최종 점수: {state['artifacts']['ensemble_result']['merged_score']}")


if __name__ == "__main__":
    simulate()
