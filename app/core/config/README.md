# app/core/config — 설정 패키지

PAZULE의 모든 런타임 설정을 단일 진입점으로 관리한다.  
**설정을 바꾸려면 이 폴더의 파일만 수정하면 된다.**

---

## 파일 구조

```
app/core/config/
├── __init__.py        # 패키지 진입점 — re-export
├── environments.py    # 환경별 설정 프로필 (dev / test / prod)
├── settings.py        # 런타임 Settings 클래스 — 단일 접근점
└── constants.py       # 변경되지 않는 정적 상수
```

---

## 설정 로드 우선순위

```
.env (환경변수)  >  environments.py 프로필  >  settings.py 기본값
```

1. `.env`에 값이 있으면 항상 우선 적용 (개별 오버라이드용)
2. 없으면 `PAZULE_ENV`가 가리키는 환경 프로필 값 사용
3. 프로필에도 없으면 `settings.py`의 하드코딩 기본값 사용

---

## 환경 선택

`.env`의 `PAZULE_ENV` 값으로 프로필을 선택한다.

| 환경 | `PAZULE_ENV` 값 | 용도 |
|------|----------------|------|
| 로컬 개발 | `development` | GPS 없는 사진, 모델 미설치 환경에서 전체 플로우 테스트 |
| pytest | `test` | `tests/conftest.py`가 자동 주입 — 직접 설정 불필요 |
| 실제 서비스 | `production` | 모든 검증·추론 활성화 |

---

## 전체 설정 항목 색인

> 자세한 설명은 `environments.py`의 주석을 참고한다.

### Dev / Debug 플래그

| 항목 | 타입 | dev | test | prod | 설명 |
|------|------|:---:|:----:|:----:|------|
| `SKIP_METADATA_VALIDATION` | `bool` | `True` | `False` | `False` | EXIF GPS·날짜 검증 건너뛰기 |
| `BYPASS_MODEL_VALIDATION` | `bool` | `True` | `False` | `False` | AI 모델 추론 건너뛰기 (score=1.0) |

### 판정 임계값 (모든 환경 동일)

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `LOCATION_PASS_THRESHOLD` | `float` | `0.70` | 위치 미션 통과 기준 점수 |
| `ATMOSPHERE_PASS_THRESHOLD` | `float` | `0.62` | 분위기 미션 통과 기준 점수 |

### 모델 선택 (모든 환경 동일)

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `MODEL_SELECTION_LOCATION` | `str` | `"siglip2"` | 위치 미션 사용 모델 (`siglip2` \| `blip` \| `ensemble`) |
| `MODEL_SELECTION_ATMOSPHERE` | `str` | `"siglip2"` | 분위기 미션 사용 모델 |
| `ENSEMBLE_MODELS_LOCATION` | `str` | `"siglip2,blip"` | 위치 앙상블 참여 모델 목록 (쉼표 구분) |
| `ENSEMBLE_MODELS_ATMOSPHERE` | `str` | `"siglip2,blip"` | 분위기 앙상블 참여 모델 목록 |

### API 제한

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `API_TIMEOUT_SECONDS` | `float` | `60.0` | 외부 API 호출 최대 대기 시간 (초) |
| `API_MAX_RETRIES` | `int` | `2` | 외부 API 호출 최대 재시도 횟수 |

### 미션 세션 정책

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `MISSION_SESSION_TTL_MINUTES` | `int` | `60` | 세션 유효 시간 (분) |
| `MISSION_MAX_SUBMISSIONS` | `int` | `3` | 세션당 최대 사진 제출 횟수 |
| `MISSION_SITE_RADIUS_METERS` | `int` | `300` | 미션 위치 허용 반경 (미터) |

### Council (교차 검증 위원회)

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `COUNCIL_ENABLED` | `bool` | `True` | Council 3-Tier 에스컬레이션 활성화 |
| `COUNCIL_BORDERLINE_MARGIN` | `float` | `0.08` | 경계값 범위 (임계값 ± margin) |

### API 키 (시크릿 — `.env` 전용)

| 항목 | 설명 |
|------|------|
| `GEMINI_API_KEY` | Google Gemini LLM (힌트 생성, 텍스트 판정) |
| `OPENROUTER_API_KEY` | OpenRouter 경유 Qwen-VL (Council Tier 3) |
| `OPENAI_API_KEY` | OpenAI API (Gemini 폴백) |

---

## 설정 접근 방법

```python
from app.core.config import settings

# 임계값 읽기
threshold = settings.LOCATION_PASS_THRESHOLD   # → 0.70

# 환경 확인
if settings.ENV == "production":
    ...

# 앙상블 모델 리스트 (파싱 포함)
models = settings.location_ensemble_models     # → ["siglip2", "blip"]
```

---

## 설정 추가 방법

1. `environments.py`의 `DEFAULT_PROFILE`에 새 키·기본값·주석 추가
2. 환경별 오버라이드가 필요하면 `PROFILES["development"]` 등에 추가
3. `settings.py`의 `Settings` 클래스에 `_env_or_profile(...)` 속성 추가
4. 이 README의 색인 테이블 업데이트
