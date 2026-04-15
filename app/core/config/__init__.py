"""Config package — re-exports for backward compatibility.

Usage:
    from app.core.config import settings          # 기존 방식 그대로
    from app.core.config import constants         # 정적 상수 모듈
    from app.core.config.constants import ALLOWED_UPLOAD_EXTENSIONS  # 직접 import
"""

from .settings import settings
from . import constants

__all__ = ["settings", "constants"]
