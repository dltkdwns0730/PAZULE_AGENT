"""PAZULE 전역 정적 상수.

런타임 환경에 따라 바뀌지 않는 값을 여기서 관리한다.
환경 변수로 제어해야 하는 값은 settings.py에 정의한다.
"""

from __future__ import annotations

# ── File Upload ────────────────────────────────────────────
ALLOWED_UPLOAD_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".heic", ".heif"}
)

# ── Ensemble Model Weights ─────────────────────────────────
# location 미션: siglip2(0.60) + blip(0.40)
LOCATION_MODEL_WEIGHTS: dict[str, float] = {"siglip2": 0.60, "blip": 0.40}
# atmosphere 미션: siglip2(0.75) + blip(0.25)
ATMOSPHERE_MODEL_WEIGHTS: dict[str, float] = {"siglip2": 0.75, "blip": 0.25}
# 레지스트리에 없는 모델의 기본 가중치
DEFAULT_MODEL_WEIGHT: float = 0.1

# ── Score Thresholds ───────────────────────────────────────
# 앙상블 내 모델 간 점수 차이가 이 값 이상이면 충돌(conflict) 플래그 설정
ENSEMBLE_CONFLICT_THRESHOLD: float = 0.35

# ── Timeout ────────────────────────────────────────────────
# API 타임아웃에 더하는 future.result() 여유 시간 (초)
MODEL_TIMEOUT_BUFFER_SECONDS: float = 5.0

# ── Coupon ─────────────────────────────────────────────────
COUPON_CODE_LENGTH: int = 8  # 쿠폰 코드 자릿수
DEFAULT_DISCOUNT_RULE: str = "10%_OFF"
