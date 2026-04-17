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
# location 미션: 정밀한 VQA(BLIP)를 주력으로 활용 (0.70)
LOCATION_MODEL_WEIGHTS: dict[str, float] = {"blip": 0.70, "siglip2": 0.30}
# atmosphere 미션: 전역 시각적 특징(SigLIP2/CLIP)을 주력으로 활용 (0.80)
ATMOSPHERE_MODEL_WEIGHTS: dict[str, float] = {"siglip2": 0.80, "blip": 0.20}
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
