# PAZULE Architecture

이 문서는 현재 코드 기준의 시스템 구조를 설명합니다. 작업 기록은 `docs/tasks/`와 `docs/changelog.md`에서 별도로 확인합니다.

## System Overview

```text
React SPA
  -> Flask API
  -> Supabase JWT authentication
  -> GPS / EXIF / image hash validation
  -> LangGraph mission judgement pipeline
  -> mission session and coupon services
  -> JSON or DB storage backend
  -> organization-scoped admin console
```

## Backend API

[app/api/routes.py](../app/api/routes.py)는 현재 16개 route를 제공합니다.

| 영역 | Route |
|---|---|
| 힌트/프리뷰 | `GET /get-today-hint`, `POST /api/preview` |
| 미션 | `POST /api/mission/start`, `POST /api/mission/submit` |
| 쿠폰 | `POST /api/coupon/issue`, `POST /api/coupon/redeem`, `GET /api/coupons` |
| 사용자 | `GET /api/user/stats`, `POST /api/user/reset` |
| 관리자 | `GET /api/admin/summary`, `GET /api/admin/organizations`, `GET /api/admin/mission-sessions`, `GET /api/admin/mission-sessions/<mission_id>`, `GET /api/admin/coupons`, `POST /api/admin/coupons/<code>/redeem`, `GET /api/admin/users` |

라우트는 HTTP 입력과 응답 경계를 담당하고, 미션/쿠폰/관리자 로직은 `app/services/`에 둡니다.

## LangGraph Pipeline

모든 노드는 `PipelineState`를 읽고 필요한 결과를 `artifacts`, `errors`, `control_flags`, `final_response`에 기록합니다.

| Node | 파일 | 역할 |
|---|---|---|
| `validator` | `app/council/nodes.py` | 이미지 존재, EXIF, GPS, 해시 중복 검증 |
| `router` | `app/council/nodes.py` | 미션 타입 정규화 |
| `evaluator` | `app/council/nodes.py` | SigLIP2/BLIP/Qwen VL adapter 실행 |
| `aggregator` | `app/council/nodes.py` | 모델 점수 가중 집계와 conflict 판단 |
| `council` | `app/council/deliberation.py` | 3-tier 교차 판정 |
| `judge` | `app/council/nodes.py` | 임계값과 council 결과로 최종 pass/fail 결정 |
| `policy` | `app/council/nodes.py` | 쿠폰 발급 가능 여부 결정 |
| `responder` | `app/council/nodes.py` | API 응답 DTO 조립 |

## Mission Judgement Defaults

| 항목 | Location | Atmosphere |
|---|---:|---:|
| 기본 모델 | `siglip2` | `siglip2` |
| 앙상블 모델 목록 | `siglip2,blip` | `siglip2,blip` |
| 앙상블 가중치 | `siglip2=0.30`, `blip=0.70` | `siglip2=0.80`, `blip=0.20` |
| 통과 임계값 | `0.70` | `0.35` |

Council은 규칙 기반 consistency 판정, threshold 경계 분석, Qwen VL fallback 판정을 단계적으로 사용합니다. Qwen VL은 conflict 또는 borderline 상황에서 비용이 드는 보조 판정으로 사용됩니다.

## Mission Session Rules

| 설정 | 기본값 |
|---|---:|
| 세션 TTL | `60`분 |
| 세션당 최대 제출 | `3`회 |
| 위치 허용 반경 | `300m` |
| 허용 GPS 정확도 | `100m` |
| 기본 사이트 좌표 | `37.711988`, `126.6867095` |

서버는 Supabase JWT에서 검증된 사용자 ID를 미션 세션의 소유자로 사용합니다. 클라이언트가 보낸 `user_id`는 신뢰 경계로 사용하지 않습니다.

## Storage

| 저장소 | 현재 경계 |
|---|---|
| JSON | `STORAGE_BACKEND=json` 기본값에서 미션 세션과 쿠폰을 파일 기반으로 처리 |
| DB | `STORAGE_BACKEND=db`에서 SQLAlchemy repository를 통해 Supabase/Postgres 또는 호환 DB 사용 |

관리자 조회는 `AdminService`가 저장소 구현을 감싸며, DB 모드에서는 `organizations`, `sites`, `organization_members`, `mission_sessions`, `coupons` 관계를 사용합니다.

## Admin Scope

| 권한 | 데이터 범위 |
|---|---|
| `platform_master` | 전체 기업, 사이트, 미션, 쿠폰, 사용자 활동 |
| `admin` | 현재 호환상 마스터 권한으로 인정 |
| organization member `owner/manager/viewer` | 소속 기업 데이터 |

관리자 프론트엔드는 `/admin`, `/admin/logs`, `/admin/logs/:missionId`, `/admin/coupons`, `/admin/users` 경로를 사용합니다.
