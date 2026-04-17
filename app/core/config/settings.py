"""PAZULE 애플리케이션 런타임 설정.

설정 로드 우선순위:
    1. 환경변수 (.env) — API 키, PAZULE_ENV 선택자
    2. environments.py 프로필 — 환경별 동작 설정 (임계값, 플래그 등)
    3. 이 파일의 기본값 — 위 두 곳에 없는 값의 폴백

사용법:
    from app.core.config import settings
    settings.LOCATION_PASS_THRESHOLD   # → 0.70
    settings.SKIP_METADATA_VALIDATION  # → 환경에 따라 True/False
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from app.core.config.environments import get_profile

load_dotenv()

# ── 현재 환경 결정 ────────────────────────────────────────────
# .env 또는 시스템 환경변수에서 PAZULE_ENV를 읽는다.
# 미설정 시 "development"로 폴백 (로컬 개발 기본).
_ENV_NAME: str = os.getenv("PAZULE_ENV", "development")
_profile: dict[str, object] = get_profile(_ENV_NAME)


def _env_or_profile(key: str, cast: type = str) -> object:
    """환경변수가 있으면 그 값을, 없으면 프로필 값을 반환한다.

    환경변수(.env)에 명시적으로 설정된 값이 프로필보다 우선한다.
    이를 통해 특정 설정만 임시로 오버라이드할 수 있다.

    Args:
        key: 환경변수 이름 (예: "LOCATION_PASS_THRESHOLD").
        cast: 반환 타입 (str, float, int, bool).

    Returns:
        환경변수 값 또는 프로필 기본값.
    """
    env_val = os.getenv(key)
    if env_val is not None:
        if cast is bool:
            return env_val.lower() == "true"
        return cast(env_val)
    return _profile[key]


class Settings:
    """PAZULE 전역 설정 인터페이스.

    모든 설정값은 이 클래스의 속성으로 접근한다.
    환경변수 → environments.py 프로필 → 기본값 순으로 결정된다.

    Attributes:
        - 시크릿(API 키): .env 전용, 프로필에 포함하지 않음
        - 동작 설정(임계값, 플래그): environments.py 프로필 기반
        - 모델 ID: .env에서 오버라이드 가능, 프로필에 기본값
    """

    # ── 메타 ─────────────────────────────────────────────────
    PROJECT_NAME: str = "PAZULE"
    VERSION: str = "2.0.0"

    # 현재 활성 환경 이름 ("development" | "test" | "production")
    ENV: str = _ENV_NAME

    # ── API 키 (시크릿 — .env 전용) ──────────────────────────
    # 이 값들은 environments.py에 넣지 않는다.
    # 코드·Git에 노출되면 안 되는 시크릿이므로 .env에서만 관리.
    #
    # GEMINI_API_KEY: Google Gemini LLM 호출에 사용.
    #   힌트 생성, 감성 검증 등 텍스트 LLM 기본 프로바이더.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    #
    # OPENROUTER_API_KEY: OpenRouter 경유 Qwen-VL 멀티모달 모델 호출에 사용.
    #   Council Tier 3 에스컬레이션 시 Qwen VL을 재호출할 때 필요.
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    #
    # OPENAI_API_KEY: OpenAI API 호출에 사용. Gemini API 미사용 시 폴백.
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ── 모델 ID ──────────────────────────────────────────────
    # 각 AI 모델의 HuggingFace 또는 API 식별자.
    # .env에서 오버라이드 가능하며, 미설정 시 아래 기본값 사용.
    #
    # BLIP_MODEL_ID: BLIP-VQA 모델. Visual Question Answering 기반 장소 판정.
    BLIP_MODEL_ID: str = "Salesforce/blip-vqa-base"
    #
    # SIGLIP2_MODEL_ID: SigLIP2 모델. Zero-shot 이미지-텍스트 매칭 기반 판정.
    #   CLIP 대비 경량화되어 로컬 GPU에서도 빠르게 추론 가능.
    SIGLIP2_MODEL_ID: str = os.getenv(
        "SIGLIP2_MODEL_ID", "google/siglip2-base-patch16-224"
    )
    #
    # QWEN_VL_MODEL_ID: Qwen Vision-Language 모델. API 호출 방식.
    #   Council Tier 3 에스컬레이션에서 경계값 케이스 재검증에 사용.
    QWEN_VL_MODEL_ID: str = os.getenv("QWEN_VL_MODEL_ID", "qwen/qwen3.6-plus:free")
    #
    # LLM_MODEL_ID: 텍스트 전용 LLM. 힌트 생성, 프롬프트 기반 판정에 사용.
    #   미설정 시 Gemini API를 기본 프로바이더로 사용.
    LLM_MODEL_ID: str = os.getenv("LLM_MODEL_ID", "")

    # ── 동작 설정 (environments.py 프로필 기반) ────────────────
    # 아래 설정들은 environments.py의 PROFILES에서 환경별로 관리된다.
    # .env에 같은 이름의 환경변수가 있으면 프로필 값을 오버라이드한다.

    # --- Dev / Debug 플래그 ---
    SKIP_METADATA_VALIDATION: bool = _env_or_profile(  # type: ignore[assignment]
        "SKIP_METADATA_VALIDATION", bool
    )
    BYPASS_MODEL_VALIDATION: bool = _env_or_profile(  # type: ignore[assignment]
        "BYPASS_MODEL_VALIDATION", bool
    )

    # --- 판정 임계값 ---
    LOCATION_PASS_THRESHOLD: float = _env_or_profile(  # type: ignore[assignment]
        "LOCATION_PASS_THRESHOLD", float
    )
    ATMOSPHERE_PASS_THRESHOLD: float = _env_or_profile(  # type: ignore[assignment]
        "ATMOSPHERE_PASS_THRESHOLD", float
    )

    # --- 모델 선택 ---
    MODEL_SELECTION_LOCATION: str = _env_or_profile(  # type: ignore[assignment]
        "MODEL_SELECTION_LOCATION", str
    )
    MODEL_SELECTION_ATMOSPHERE: str = _env_or_profile(  # type: ignore[assignment]
        "MODEL_SELECTION_ATMOSPHERE", str
    )
    ENSEMBLE_MODELS_LOCATION: str = _env_or_profile(  # type: ignore[assignment]
        "ENSEMBLE_MODELS_LOCATION", str
    )
    ENSEMBLE_MODELS_ATMOSPHERE: str = _env_or_profile(  # type: ignore[assignment]
        "ENSEMBLE_MODELS_ATMOSPHERE", str
    )

    # --- API 제한 ---
    API_TIMEOUT_SECONDS: float = _env_or_profile(  # type: ignore[assignment]
        "API_TIMEOUT_SECONDS", float
    )
    API_MAX_RETRIES: int = _env_or_profile(  # type: ignore[assignment]
        "API_MAX_RETRIES", int
    )

    # --- 미션 세션 정책 ---
    MISSION_SESSION_TTL_MINUTES: int = _env_or_profile(  # type: ignore[assignment]
        "MISSION_SESSION_TTL_MINUTES", int
    )
    MISSION_MAX_SUBMISSIONS: int = _env_or_profile(  # type: ignore[assignment]
        "MISSION_MAX_SUBMISSIONS", int
    )
    MISSION_SITE_RADIUS_METERS: int = _env_or_profile(  # type: ignore[assignment]
        "MISSION_SITE_RADIUS_METERS", int
    )

    # --- Council ---
    COUNCIL_ENABLED: bool = _env_or_profile(  # type: ignore[assignment]
        "COUNCIL_ENABLED", bool
    )
    COUNCIL_BORDERLINE_MARGIN: float = _env_or_profile(  # type: ignore[assignment]
        "COUNCIL_BORDERLINE_MARGIN", float
    )

    # ── 경로 설정 (환경 무관, 코드 내 고정) ────────────────────
    #
    # BASE_DIR: 프로젝트 루트 디렉터리 절대 경로.
    #   pyproject.toml이 위치한 디렉터리를 가리킨다.
    BASE_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    #
    # DATA_DIR: JSON 데이터 파일 저장 디렉터리 (쿠폰, 세션 등).
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    #
    # PROMPT_TEMPLATES_DIR: LLM 프롬프트 YAML 템플릿 디렉터리.
    PROMPT_TEMPLATES_DIR: str = os.path.join(BASE_DIR, "app", "prompts", "templates")

    @property
    def LANDMARK_QA_PATH(self) -> str:
        """로컬 테스트용 랜드마크 QA 데이터셋 파일의 절대 경로를 반환한다.

        Returns:
            landmark_qa_labeled.json 파일 경로.
        """
        return os.path.join(self.DATA_DIR, "landmark_qa_labeled.json")

    @staticmethod
    def parse_csv(value: str) -> list[str]:
        """쉼표(,)로 구분된 문자열을 파싱하여 소문자 리스트로 반환한다.

        Args:
            value: 파싱할 CSV 형태의 문자열 (예: "siglip2,blip").

        Returns:
            공백이 제거된 소문자 토큰 리스트 (예: ["siglip2", "blip"]).
        """
        return [token.strip().lower() for token in value.split(",") if token.strip()]

    @property
    def location_ensemble_models(self) -> list[str]:
        """위치(Location) 미션 앙상블에 참여할 모델 이름 리스트를 반환한다.

        Returns:
            앙상블 모델 식별자 리스트 (예: ["siglip2", "blip"]).
        """
        return self.parse_csv(self.ENSEMBLE_MODELS_LOCATION)

    @property
    def atmosphere_ensemble_models(self) -> list[str]:
        """분위기(Atmosphere) 미션 앙상블에 참여할 모델 이름 리스트를 반환한다.

        Returns:
            앙상블 모델 식별자 리스트 (예: ["siglip2", "blip"]).
        """
        return self.parse_csv(self.ENSEMBLE_MODELS_ATMOSPHERE)


settings = Settings()
