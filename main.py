# =============================================================================
# PAZULE Backend Entry Point
# =============================================================================
#
# [로컬 개발 서버 실행]
#
#   1. 가상환경 활성화 (uv 사용 권장):
#      > .\.venv\Scripts\activate          # Windows
#      $ source .venv/bin/activate       # macOS/Linux
#
#   2. 의존성 설치:
#      > uv pip install ".[dev,model]"   # 모델 포함 전체 설치
#      > uv pip install "."              # API 모드만 (모델 제외)
#
#   3. 환경변수 설정 (.env 파일):
#      OPENAI_API_KEY=sk-...             # Qwen/LLM 모델용 API 키
#      MODEL_SELECTION_LOCATION=blip     # 단일 모델 or 'ensemble'
#      MODEL_SELECTION_ATMOSPHERE=ensemble
#
#   4. 백엔드 서버 실행:
#      > python main.py                  # → http://localhost:8080
#
# [프론트엔드 서버 실행 (별도 터미널)]
#
#   > cd front
#   > npm install                        # 최초 1회
#   > npm run dev                        # → http://localhost:5173
#
#   ※ Vite 개발 서버가 /api/* 요청을 8080 포트로 프록시합니다.
#
# =============================================================================
#
# [파이프라인 직접 실행 (Python 스크립트에서)]
#
#   from app.council.graph import pipeline_app
#
#   initial_state = {
#       "request_context": {
#           "mission_id":   "test-session-001",       # 세션 식별자
#           "user_id":      "dev-user",
#           "site_id":      "pazule-default",
#           "mission_type": "location",                # "location" | "atmosphere"
#           "image_path":   "/path/to/photo.jpg",      # 절대경로 또는 상대경로
#           "answer":       "한길책박물관",              # 오늘의 정답 키워드
#           "model_selection": None,                   # None이면 .env 기본값 사용
#       },
#       "artifacts":      {},
#       "errors":         [],
#       "control_flags":  {},
#       "messages":       [],
#   }
#
#   output = pipeline_app.invoke(initial_state)
#
#   # 결과 확인
#   final = output.get("final_response", {}).get("data", {})
#   print(final)
#   # → {
#   #     "success":        True,
#   #     "score":          0.87,
#   #     "message":        "위치가 확인되었습니다.",
#   #     "couponEligible": True,
#   #     "traces":         [...],
#   #   }
#
#   ※ CLI 시뮬레이션 스크립트: uv run scripts/simulate_cli.py
#   ※ 실제 모델 성능 테스트:   uv run scripts/test_real_models.py
#   ※ 목 파이프라인 테스트:    uv run scripts/test_pipeline_mock.py
#
# =============================================================================

from flask import Flask
from flask_cors import CORS

from app.api.routes import api
from app.core.config import settings


def create_app():
    # 1. 프롬프트 레지스트리 초기화
    from app.prompts.registry import PromptRegistry

    registry = PromptRegistry.get_instance()
    registry.load_all(settings.PROMPT_TEMPLATES_DIR)

    # 2. 모델 레지스트리 초기화
    from app.models.model_registry import register_default_models

    register_default_models()

    # 3. 미션 플러그인 등록
    from app.plugins.registry import register_default_plugins

    register_default_plugins()

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(api)
    return app


if __name__ == "__main__":
    app = create_app()
    print(f"{settings.PROJECT_NAME} v{settings.VERSION} 서버 실행 중 (포트 8080)...")
    app.run(host="0.0.0.0", port=8080)
