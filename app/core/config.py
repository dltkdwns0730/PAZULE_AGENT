import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "PAZULE"
    VERSION: str = "2.0.0"

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Model Configuration
    BLIP_MODEL_ID: str = "Salesforce/blip-vqa-base"

    # Path Configuration
    BASE_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    DATA_DIR: str = os.path.join(BASE_DIR, "data")

    @property
    def LANDMARK_QA_PATH(self):
        return os.path.join(self.DATA_DIR, "landmark_qa_labeled.json")


settings = Settings()
