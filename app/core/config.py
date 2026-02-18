"""Intent: ??? ?? ??? ??? ???
Used by: ?? ??? ??/???/??????? ???
Flow: ?? ?? ??? ???? ??? ???? ???"""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Purpose: `Settings` ??? ??? ?? ??? ???
    Context: ?? ???? ?? ??? ??? ??
    Attrs: ?? ?? ???? ?? ??? ???"""
    PROJECT_NAME: str = "PAZULE"
    VERSION: str = "2.0.0"

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Model Configuration
    BLIP_MODEL_ID: str = "Salesforce/blip-vqa-base"
    CLIP_MODEL_ID: str = os.getenv("CLIP_MODEL_ID", "openai/clip-vit-base-patch32")
    SIGLIP2_MODEL_ID: str = os.getenv(
        "SIGLIP2_MODEL_ID", "google/siglip2-base-patch16-224"
    )
    QWEN_VL_MODEL_ID: str = os.getenv("QWEN_VL_MODEL_ID", "Qwen/Qwen2.5-VL-7B-Instruct")

    # Runtime model selection
    MODEL_SELECTION_LOCATION: str = os.getenv("MODEL_SELECTION_LOCATION", "blip")
    MODEL_SELECTION_ATMOSPHERE: str = os.getenv(
        "MODEL_SELECTION_ATMOSPHERE", "ensemble"
    )
    ENSEMBLE_MODELS_LOCATION: str = os.getenv(
        "ENSEMBLE_MODELS_LOCATION", "blip,qwen,clip"
    )
    ENSEMBLE_MODELS_ATMOSPHERE: str = os.getenv(
        "ENSEMBLE_MODELS_ATMOSPHERE", "siglip2,qwen,blip,clip"
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

    # Path Configuration
    BASE_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    DATA_DIR: str = os.path.join(BASE_DIR, "data")

    @property
    def LANDMARK_QA_PATH(self):
        """Caller: ?? ?? ???? ???
        Purpose: `LANDMARK_QA_PATH` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: None
        Note: ?? ?? ?? ???? ???"""
        return os.path.join(self.DATA_DIR, "landmark_qa_labeled.json")

    @staticmethod
    def parse_csv(value: str) -> list[str]:
        """Caller: ?? ?? ???? ???
        Purpose: `parse_csv` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: value: ???? ???? ??
        Note: ?? ?? ?? ???? ???"""
        return [token.strip().lower() for token in value.split(",") if token.strip()]

    @property
    def location_ensemble_models(self) -> list[str]:
        """Caller: ?? ?? ???? ???
        Purpose: `location_ensemble_models` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: None
        Note: ?? ?? ?? ???? ???"""
        return self.parse_csv(self.ENSEMBLE_MODELS_LOCATION)

    @property
    def atmosphere_ensemble_models(self) -> list[str]:
        """Caller: ?? ?? ???? ???
        Purpose: `atmosphere_ensemble_models` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: None
        Note: ?? ?? ?? ???? ???"""
        return self.parse_csv(self.ENSEMBLE_MODELS_ATMOSPHERE)


settings = Settings()
