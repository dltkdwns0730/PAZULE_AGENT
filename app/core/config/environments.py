"""PAZULE 환경별 설정 프로필.

모든 동작 제어 설정을 환경(development / test / production)별로 정의한다.
.env 파일에는 API 키(시크릿)와 PAZULE_ENV 선택자만 남기고,
나머지 설정은 이 파일에서 중앙 관리한다.

사용법:
    # .env에서 PAZULE_ENV=development 설정
    # settings.py가 자동으로 해당 프로필을 로드

프로필 추가:
    PROFILES 딕셔너리에 새 환경 이름을 키로 추가하면 된다.
    모든 키는 DEFAULT_PROFILE의 키와 동일해야 한다.
"""

from __future__ import annotations

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 기본 프로필 (모든 환경의 베이스)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFAULT_PROFILE: dict[str, object] = {
    # ── Dev / Debug 플래그 ───────────────────────────────────
    #
    # SKIP_METADATA_VALIDATION (bool)
    #   True  → EXIF GPS 좌표·촬영 날짜 검증을 완전히 건너뛴다.
    #           GPS가 없는 사진이나 과거 사진으로 로컬 테스트할 때 사용.
    #   False → 실제 EXIF 메타데이터를 검증한다. (프로덕션 기본값)
    #
    "SKIP_METADATA_VALIDATION": False,
    #
    # BYPASS_MODEL_VALIDATION (bool)
    #   True  → AI 모델(SigLIP2·BLIP) 추론을 건너뛰고 score=1.0으로
    #           항상 통과 처리한다. 모델 없이 전체 UI 플로우를 테스트할 때 사용.
    #   False → 실제 비전 모델 추론을 수행한다. (프로덕션 기본값)
    #
    "BYPASS_MODEL_VALIDATION": False,
    # ── 판정 임계값 (Decision Thresholds) ────────────────────
    #
    # LOCATION_PASS_THRESHOLD (float, 0.0 ~ 1.0)
    #   위치(Location) 미션에서 앙상블 최종 점수가 이 값 이상이면 "통과".
    #   값을 낮추면 통과가 쉬워지고, 높이면 엄격해진다.
    #   기준: SigLIP2(0.60) + BLIP(0.40) 가중합 기반.
    #
    "LOCATION_PASS_THRESHOLD": 0.70,
    #
    # ATMOSPHERE_PASS_THRESHOLD (float, 0.0 ~ 1.0)
    #   분위기(Atmosphere) 미션에서 앙상블 최종 점수가 이 값 이상이면 "통과".
    #   분위기 판정은 주관적이므로 위치보다 낮게 설정.
    #   기준: SigLIP2(0.80) + BLIP(0.20) 가중합 기반.
    #   v2.6.1: 벤치마크 결과(0.3~0.5)를 반영하여 0.62에서 0.35로 하향 조정.
    #
    "ATMOSPHERE_PASS_THRESHOLD": 0.35,
    # ── 모델 선택 (Model Selection) ──────────────────────────
    #
    # MODEL_SELECTION_LOCATION (str)
    #   위치 미션에 사용할 모델 또는 전략.
    #   "siglip2"  → SigLIP2 단독 사용
    #   "blip"     → BLIP-VQA 단독 사용
    #   "ensemble" → settings.ENSEMBLE_MODELS_LOCATION에 정의된 모델 조합
    #
    "MODEL_SELECTION_LOCATION": "siglip2",
    #
    # MODEL_SELECTION_ATMOSPHERE (str)
    #   분위기 미션에 사용할 모델 또는 전략. 옵션은 위와 동일.
    #
    "MODEL_SELECTION_ATMOSPHERE": "siglip2",
    #
    # ENSEMBLE_MODELS_LOCATION (str, 쉼표 구분)
    #   위치 미션 앙상블에 참여할 모델 목록.
    #   예: "siglip2,blip" → SigLIP2 + BLIP 앙상블 투표.
    #   가중치는 constants.LOCATION_MODEL_WEIGHTS에서 정의.
    #
    "ENSEMBLE_MODELS_LOCATION": "siglip2,blip",
    #
    # ENSEMBLE_MODELS_ATMOSPHERE (str, 쉼표 구분)
    #   분위기 미션 앙상블에 참여할 모델 목록.
    #   가중치는 constants.ATMOSPHERE_MODEL_WEIGHTS에서 정의.
    #
    "ENSEMBLE_MODELS_ATMOSPHERE": "siglip2,blip",
    # ── API 제한 (Timeout & Retries) ─────────────────────────
    #
    # API_TIMEOUT_SECONDS (float, 초)
    #   외부 API 호출(Qwen VL 등) 시 최대 대기 시간.
    #   이 시간을 초과하면 타임아웃 에러로 처리한다.
    #   모델 future에는 이 값 + constants.MODEL_TIMEOUT_BUFFER_SECONDS가 적용됨.
    #
    "API_TIMEOUT_SECONDS": 60.0,
    #
    # API_MAX_RETRIES (int)
    #   외부 API 호출 실패 시 최대 재시도 횟수.
    #   0이면 재시도 없이 즉시 실패 처리.
    #
    "API_MAX_RETRIES": 2,
    # ── 미션 세션 정책 (Session & Policy) ─────────────────────
    #
    # MISSION_SESSION_TTL_MINUTES (int, 분)
    #   미션 세션의 유효 시간. 이 시간이 지나면 세션이 만료되어
    #   새로 시작해야 한다.
    #
    "MISSION_SESSION_TTL_MINUTES": 60,
    #
    # MISSION_MAX_SUBMISSIONS (int)
    #   하나의 미션 세션에서 사진을 제출할 수 있는 최대 횟수.
    #   초과하면 세션을 새로 시작해야 한다.
    #
    "MISSION_MAX_SUBMISSIONS": 3,
    #
    # MISSION_SITE_RADIUS_METERS (int, 미터)
    #   미션 대상 위치로부터 허용되는 GPS 반경.
    #   이 범위 밖에서 촬영한 사진은 위치 검증에서 실패한다.
    #
    "MISSION_SITE_RADIUS_METERS": 300,
    "MISSION_SITE_LAT": 37.711988,
    "MISSION_SITE_LON": 126.6867095,
    "MISSION_GPS_MAX_ACCURACY_METERS": 100,
    "SKIP_GPS_VALIDATION": False,
    # ── Council (교차 검증 위원회) ────────────────────────────
    #
    # COUNCIL_ENABLED (bool)
    #   True  → 앙상블 투표 후 Council 3-Tier 에스컬레이션을 활성화한다.
    #           경계값 케이스에서 Qwen VL API를 재호출해 정확도를 높인다.
    #   False → Council 단계를 건너뛰고 앙상블 점수만으로 판정한다.
    #
    "COUNCIL_ENABLED": True,
    #
    # COUNCIL_BORDERLINE_MARGIN (float, 0.0 ~ 1.0)
    #   앙상블 점수가 (임계값 - margin) ~ (임계값 + margin) 범위에 있으면
    #   "경계값 케이스"로 분류해 Council 에스컬레이션을 트리거한다.
    #   예: 임계값 0.70, margin 0.08 → 0.62~0.78 범위가 경계값.
    #
    "COUNCIL_BORDERLINE_MARGIN": 0.08,
    "DATABASE_URL": "sqlite:///data/pazule.db",
    "SUPABASE_URL": "",
    "SUPABASE_JWKS_URL": "",
    "SUPABASE_JWT_AUDIENCE": "authenticated",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 환경별 프로필 (DEFAULT_PROFILE을 기반으로 오버라이드)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROFILES: dict[str, dict[str, object]] = {
    # ── development ──────────────────────────────────────────
    # 로컬 개발 환경. GPS 없는 사진, AI 모델 미설치 상태에서도
    # 전체 플로우를 테스트할 수 있도록 검증을 우회한다.
    "development": {
        **DEFAULT_PROFILE,
        "SKIP_METADATA_VALIDATION": True,  # GPS·날짜 검증 건너뛰기
        "BYPASS_MODEL_VALIDATION": True,  # AI 추론 건너뛰기 (score=1.0)
    },
    # ── test ─────────────────────────────────────────────────
    # pytest 실행 환경. 모든 검증 로직이 활성화되어야 mock이
    # 정상 동작한다. dev 플래그가 True이면 mock이 호출되지 않아
    # 테스트가 깨진다.
    "test": {
        **DEFAULT_PROFILE,
        "SKIP_METADATA_VALIDATION": False,  # 검증 활성화 (mock으로 대체)
        "BYPASS_MODEL_VALIDATION": False,  # 추론 활성화 (mock으로 대체)
    },
    # ── production ───────────────────────────────────────────
    # 실제 서비스 환경. 모든 검증·추론이 활성화된다.
    # 이 프로필에서 SKIP/BYPASS가 True가 되면 보안 사고.
    "production": {
        **DEFAULT_PROFILE,
        "SKIP_METADATA_VALIDATION": False,  # 실제 EXIF 검증
        "BYPASS_MODEL_VALIDATION": False,  # 실제 AI 모델 추론
    },
}


def get_profile(env_name: str) -> dict[str, object]:
    """환경 이름에 해당하는 설정 프로필을 반환한다.

    존재하지 않는 환경 이름이면 production 프로필을 반환한다.
    알 수 없는 환경에서 dev 플래그가 켜지는 것을 방지하기 위해
    가장 엄격한 production을 폴백으로 사용한다.

    Args:
        env_name: 환경 이름 ("development", "test", "production").

    Returns:
        해당 환경의 설정 딕셔너리.
    """
    return PROFILES.get(env_name, PROFILES["production"])
