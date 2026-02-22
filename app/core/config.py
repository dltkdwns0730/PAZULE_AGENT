"""PAZULE 애플리케이션의 핵심 설정을 관리하는 모듈.
전역 환경 변수(.env)와 모델 선택, 디렉토리 경로 등을 중앙에서 통제합니다.
의존성: python-dotenv"""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """환경 변수 및 상수값을 로드하여 저장하는 데이터 인터페이스.
    LLM/VLM 모델명, 앙상블 조합, 미션 정책 임계값(Threshold) 등을 정의합니다."""
    PROJECT_NAME: str = "PAZULE"
    VERSION: str = "2.0.0"

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Model Configuration
    BLIP_MODEL_ID: str = "Salesforce/blip-vqa-base"
    SIGLIP2_MODEL_ID: str = os.getenv(
        "SIGLIP2_MODEL_ID", "google/siglip2-base-patch16-224"
    )
    QWEN_VL_MODEL_ID: str = os.getenv("QWEN_VL_MODEL_ID", "qwen/qwen-2.5-vl-7b-instruct:free")
    LLM_MODEL_ID: str = os.getenv("LLM_MODEL_ID", "")

    # Runtime model selection
    MODEL_SELECTION_LOCATION: str = os.getenv("MODEL_SELECTION_LOCATION", "siglip2")
    MODEL_SELECTION_ATMOSPHERE: str = os.getenv(
        "MODEL_SELECTION_ATMOSPHERE", "siglip2"
    )
    ENSEMBLE_MODELS_LOCATION: str = os.getenv(
        "ENSEMBLE_MODELS_LOCATION", "siglip2,blip"
    )
    ENSEMBLE_MODELS_ATMOSPHERE: str = os.getenv(
        "ENSEMBLE_MODELS_ATMOSPHERE", "siglip2,blip"
    )

    # Decision thresholds
    LOCATION_PASS_THRESHOLD: float = float(
        os.getenv("LOCATION_PASS_THRESHOLD", "0.70")
    )
    ATMOSPHERE_PASS_THRESHOLD: float = float(
        os.getenv("ATMOSPHERE_PASS_THRESHOLD", "0.62")
    )

    # Session / policy
    MISSION_SESSION_TTL_MINUTES: int = int(
        os.getenv("MISSION_SESSION_TTL_MINUTES", "60")
    )
    MISSION_MAX_SUBMISSIONS: int = int(os.getenv("MISSION_MAX_SUBMISSIONS", "3"))
    MISSION_SITE_RADIUS_METERS: int = int(
        os.getenv("MISSION_SITE_RADIUS_METERS", "300")
    )

    # Council
    COUNCIL_ENABLED: bool = os.getenv("COUNCIL_ENABLED", "true").lower() == "true"
    COUNCIL_BORDERLINE_MARGIN: float = float(
        os.getenv("COUNCIL_BORDERLINE_MARGIN", "0.08")
    )

    # Path Configuration
    BASE_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    PROMPT_TEMPLATES_DIR: str = os.path.join(
        BASE_DIR, "app", "prompts", "templates"
    )

    @property
    def LANDMARK_QA_PATH(self):
        """로컬 테스트용 랜드마크 QA 데이터셋 파일의 절대 경로를 반환합니다.
        
        Returns:
            str: landmark_qa_labeled.json 파일 경로
        """
        return os.path.join(self.DATA_DIR, "landmark_qa_labeled.json")

    @staticmethod
    def parse_csv(value: str) -> list[str]:
        """쉼표(,)로 구분된 환경 변수 문자열을 파싱하여 소문자 리스트로 반환합니다.

        Args:
            value (str): 파싱할 CSV 형태의 문자열
            
        Returns:
            list[str]: 공백이 제거된 소문자 토큰 리스트
        """
        return [token.strip().lower() for token in value.split(",") if token.strip()]

    @property
    def location_ensemble_models(self) -> list[str]:
        """위치(Location) 미션 앙상블에 참여할 모델 이름 리스트를 반환합니다.
        
        Returns:
            list[str]: 앙상블 모델 식별자 리스트
        """
        return self.parse_csv(self.ENSEMBLE_MODELS_LOCATION)

    @property
    def atmosphere_ensemble_models(self) -> list[str]:
        """분위기(Atmosphere) 미션 앙상블에 참여할 모델 이름 리스트를 반환합니다.
        
        Returns:
            list[str]: 앙상블 모델 식별자 리스트
        """
        return self.parse_csv(self.ENSEMBLE_MODELS_ATMOSPHERE)


settings = Settings()
