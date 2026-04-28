# app/core/config Settings

`app/core/config`는 PAZULE 백엔드 설정의 단일 진입점입니다. 환경 변수, 환경 프로필, 정적 상수를 이 패키지에서 확인합니다.

## Files

| 파일 | 역할 |
|---|---|
| `__init__.py` | `settings`, `constants` re-export |
| `environments.py` | `development`, `test`, `production` 프로필 기본값 |
| `settings.py` | 환경 변수와 프로필을 합쳐 `Settings` 객체로 제공 |
| `constants.py` | 모델 가중치, 쿠폰 코드 길이 등 정적 상수 |

## Load Priority

```text
.env / process environment
  -> environments.py profile selected by PAZULE_ENV
  -> settings.py fallback defaults
```

`.env` 또는 프로세스 환경 변수가 있으면 항상 우선 적용됩니다. 없으면 `PAZULE_ENV`가 가리키는 프로필 값이 사용됩니다.

## Backend Virtual Environment

백엔드 설정은 프로젝트 루트의 `.env`와 현재 shell 환경 변수를 읽습니다.
터미널에서 동일한 가상환경을 명확히 사용하려면 아래 순서로 실행합니다.

Windows PowerShell:

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv sync --dev
uv run python main.py
```

macOS/Linux:

```bash
uv venv
source .venv/bin/activate
uv sync --dev
uv run python main.py
```

이미 `.venv`가 있으면 `uv venv`는 다시 실행하지 않아도 됩니다.
가상환경을 활성화하지 않아도 `uv run pytest`, `uv run python main.py`처럼
`uv run`을 사용하면 프로젝트 가상환경 기준으로 실행됩니다.

## Current Defaults

### Environment Flags

| 설정 | development | test | production |
|---|---:|---:|---:|
| `SKIP_METADATA_VALIDATION` | `True` | `False` | `False` |
| `BYPASS_MODEL_VALIDATION` | `True` | `False` | `False` |
| `DEMO_AUTH_ENABLED` | `True` | `False` | `False` |

### Mission Judgement

| 설정 | 기본값 | 설명 |
|---|---:|---|
| `LOCATION_PASS_THRESHOLD` | `0.70` | 위치 미션 통과 기준 |
| `ATMOSPHERE_PASS_THRESHOLD` | `0.35` | 분위기 미션 통과 기준 |
| `MODEL_SELECTION_LOCATION` | `siglip2` | 위치 미션 기본 모델 |
| `MODEL_SELECTION_ATMOSPHERE` | `siglip2` | 분위기 미션 기본 모델 |
| `ENSEMBLE_MODELS_LOCATION` | `siglip2,blip` | 위치 앙상블 모델 목록 |
| `ENSEMBLE_MODELS_ATMOSPHERE` | `siglip2,blip` | 분위기 앙상블 모델 목록 |

### Model Weights

| 상수 | 현재값 |
|---|---|
| `LOCATION_MODEL_WEIGHTS` | `blip=0.70`, `siglip2=0.30` |
| `ATMOSPHERE_MODEL_WEIGHTS` | `siglip2=0.80`, `blip=0.20` |
| `ENSEMBLE_CONFLICT_THRESHOLD` | `0.35` |

### Mission Session

| 설정 | 기본값 |
|---|---:|
| `MISSION_SESSION_TTL_MINUTES` | `60` |
| `MISSION_MAX_SUBMISSIONS` | `3` |
| `MISSION_SITE_RADIUS_METERS` | `300` |
| `MISSION_SITE_LAT` | `37.711988` |
| `MISSION_SITE_LON` | `126.6867095` |
| `MISSION_GPS_MAX_ACCURACY_METERS` | `100` |

### Storage and Auth

| 설정 | 기본값 |
|---|---|
| `DATABASE_URL` | `sqlite:///data/pazule.db` |
| `STORAGE_BACKEND` | `json` |
| `SUPABASE_URL` | empty string |
| `SUPABASE_JWKS_URL` | empty string |
| `SUPABASE_JWT_AUDIENCE` | `authenticated` |

## Demo Auth

`DEMO_AUTH_ENABLED=true`이면 백엔드는 아래 bearer token을 Supabase JWT 대신 허용합니다.

| Token | Principal |
|---|---|
| `demo-user-token` | `demo-user@pazule.demo`, 일반 사용자 |
| `demo-admin-token` | `demo-admin@pazule.demo`, `platform_master` 관리자 |

이 설정은 clone-and-run 데모용이며 `production` 프로필에서는 기본값이 `False`입니다.

## Usage

```python
from app.core.config import settings

threshold = settings.LOCATION_PASS_THRESHOLD
models = settings.location_ensemble_models
```

새 설정을 추가할 때는 `environments.py`, `settings.py`, 이 README를 함께 갱신합니다.
