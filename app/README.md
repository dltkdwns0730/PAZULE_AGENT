# app/ Backend Package

`app/`는 PAZULE 백엔드의 Flask API, LangGraph 미션 판정 파이프라인, 인증/DB 경계, 비즈니스 서비스를 포함합니다.

## Request Flow

```text
HTTP request
  -> app/api/routes.py
  -> auth, GPS, EXIF, hash validation
  -> app/council/graph.py LangGraph pipeline
  -> mission session / coupon / admin services
  -> HTTP response
```

## Current API Surface

[app/api/routes.py](./api/routes.py)는 현재 16개 Flask route를 제공합니다.

| 영역 | Route |
|---|---|
| 힌트/프리뷰 | `GET /get-today-hint`, `POST /api/preview` |
| 미션 | `POST /api/mission/start`, `POST /api/mission/submit` |
| 쿠폰 | `POST /api/coupon/issue`, `POST /api/coupon/redeem`, `GET /api/coupons` |
| 사용자 | `GET /api/user/stats`, `POST /api/user/reset` |
| 관리자 | `GET /api/admin/summary`, `GET /api/admin/organizations`, `GET /api/admin/mission-sessions`, `GET /api/admin/mission-sessions/<mission_id>`, `GET /api/admin/coupons`, `POST /api/admin/coupons/<code>/redeem`, `GET /api/admin/users` |

라우트 파일은 HTTP 입력 검증과 응답 조립만 담당하고, 실제 비즈니스 로직은 `services/`와 `council/`로 분리합니다.

## Main Packages

| 경로 | 역할 |
|---|---|
| `api/` | Flask route와 요청/응답 경계 |
| `core/config/` | 환경 프로필, 설정, 정적 상수 |
| `council/` | LangGraph 기반 AI 판정 파이프라인 |
| `db/` | SQLAlchemy 모델, 세션, repository |
| `metadata/` | EXIF, GPS, 촬영일 검증 |
| `models/` | SigLIP2, BLIP, Qwen VL, LLM adapter |
| `prompts/` | YAML prompt template과 registry |
| `security/` | Supabase JWT 검증 |
| `services/` | 미션 세션, 쿠폰, 정답, 관리자 운영 서비스 |
| `legacy/` | 현재 API 경로에서 직접 호출하지 않는 호환 코드 |

## Key Services

| 파일 | 역할 |
|---|---|
| `services/answer_service.py` | 오늘의 위치/분위기 미션 정답과 힌트 조회 |
| `services/mission_session_service.py` | 미션 세션 생성, 제출 기록, 만료/제출 횟수/중복 해시 검증 |
| `services/coupon_service.py` | 쿠폰 발급, 조회, 사용 처리. `STORAGE_BACKEND`에 따라 JSON 또는 DB 저장소 사용 |
| `services/admin_service.py` | 기업 스코프가 적용된 관리자 요약, 미션, 쿠폰, 사용자 조회 |

## Current Defaults

| 설정 | 기본값 |
|---|---|
| `LOCATION_PASS_THRESHOLD` | `0.70` |
| `ATMOSPHERE_PASS_THRESHOLD` | `0.35` |
| `MODEL_SELECTION_LOCATION` | `siglip2` |
| `MODEL_SELECTION_ATMOSPHERE` | `siglip2` |
| `MISSION_SESSION_TTL_MINUTES` | `60` |
| `MISSION_MAX_SUBMISSIONS` | `3` |
| `MISSION_SITE_RADIUS_METERS` | `300` |
| `MISSION_GPS_MAX_ACCURACY_METERS` | `100` |
| `STORAGE_BACKEND` | `json` |
| `DEMO_AUTH_ENABLED` | `development=True`, `test/production=False` |

정확한 설정 원천은 [core/config/environments.py](./core/config/environments.py)와 [core/config/constants.py](./core/config/constants.py)입니다.

## Coding Rules

- route에는 복잡한 비즈니스 로직을 넣지 않습니다.
- 설정값과 매직 넘버는 `app/core/config`를 기준으로 관리합니다.
- 외부 API, 모델 추론, 파일/DB I/O는 테스트에서 mock하거나 repository/service 경계로 격리합니다.
- 백엔드 테스트 기준은 [tests/README.md](../tests/README.md)를 따릅니다.
