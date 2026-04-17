"""Config package — re-exports for backward compatibility.

Usage:
    from app.core.config import settings          # 기존 방식 그대로
    from app.core.config import constants         # 정적 상수 모듈
    from app.core.config import environments      # 환경별 설정 프로필
    from app.core.config.constants import ALLOWED_UPLOAD_EXTENSIONS  # 직접 import
    from app.core.config.environments import get_profile             # 프로필 직접 호출
"""

from . import constants
from . import environments
from .settings import settings

__all__ = ["settings", "constants", "environments"]
