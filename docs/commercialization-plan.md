# PAZULE 상용화 전략

> **분류**: 전략 · **버전**: v1 · **최종 수정**: 2026-04-07
>
> 현재 버전 v2.0.0 (Flask + LangGraph + SigLIP2/BLIP/Qwen 앙상블) 기준 프로덕션 전환 설계.

---

## 1. 현재 시스템 기능 전체 요약

### 1.1 미션 파이프라인 (LangGraph)

```
사진 업로드
  → validator     : EXIF 날짜(오늘 여부) + GPS BBox(파주출판단지) + 이미지 해시 중복 검사
  → router        : mission_type 정규화 (photo → atmosphere)
  → evaluator     : 단일 or 앙상블 모델 실행 (SigLIP2 / BLIP / Qwen-VL)
  → aggregator    : 가중 평균 merged_score + 모델 간 conflict 감지
  → council       : 3-Tier 위원회 심사
                    Tier 1 ConsistencyJudge  (규칙 기반, API 호출 없음)
                    Tier 2 ThresholdJudge    (경계값·충돌 분석, API 호출 없음)
                    Tier 3 QwenFallbackJudge (borderline일 때만 Qwen-VL 추가 호출)
  → judge         : 최종 pass/fail + council 교차검증 + manual_review 플래그
  → policy        : 비즈니스 정책 필터 (중복 이미지 재차 차단, discount_rule 결정)
  → responder     : 프론트엔드용 DTO 조립 (ui_theme: confetti/encouragement/error)
```

### 1.2 미션 타입별 모델 전략

| | Location | Atmosphere |
|---|---|---|
| 목표 | 업로드 사진이 목표 장소와 일치하는가 | 업로드 사진이 목표 감성 키워드와 일치하는가 |
| 기본 모델 | SigLIP2 | SigLIP2 |
| 앙상블 구성 | SigLIP2(60%) + BLIP(40%) | SigLIP2(75%) + BLIP(25%) |
| 통과 임계값 | 0.70 | 0.62 |
| Qwen 투입 조건 | borderline(±0.08) or conflict | 동일 |

### 1.3 Anti-Abuse 레이어

- **EXIF 날짜 검증**: 오늘 촬영 사진만 허용
- **GPS BBox 검증**: 파주출판단지 경계(37.704316–37.719660 N, 126.683397–126.690022 E) 내부만 허용
- **SHA-256 이미지 해시**: 유저당 중복 사진 재제출 차단
- **세션 TTL**: 기본 60분, 최대 3회 제출

### 1.4 쿠폰 라이프사이클

```
mission/start → mission/submit → coupon/issue → coupon/redeem
  (created)       (submitted)      (issued)        (redeemed | expired)
```
- `mission_id` 기반 멱등 발급 (중복 발급 방지)
- 쿠폰 만료: 발급 후 7일
- 파트너 POS ID로 상태 전이 감사 로그

### 1.5 현재 인프라 구성 (개발 단계)

```
Backend  : Flask + LangGraph (단일 프로세스, 포트 8080)
Frontend : React 19 + Vite SPA (포트 5173, /api/* 프록시)
모델 로딩 : 프로세스 내 지연 로드 (BLIP, SigLIP2, Qwen-VL)
영속성   : JSON 파일 (data/mission_sessions.json, data/coupons.json)
설정     : .env 파일 (OPENAI_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY)
```

---

## 2. 현재 시스템의 프로덕션 한계점

| 분류 | 문제 | 임계 시나리오 |
|---|---|---|
| **영속성** | JSON 파일 기반 세션/쿠폰 저장 | 서버 재시작 시 데이터 유실 위험, 동시 요청 race condition |
| **확장성** | Flask 단일 프로세스 | 동시 요청 수십 건 이상 시 블로킹 |
| **모델 서빙** | 모델을 API 서버 내부에서 직접 로드 | GPU 메모리 고정 점유, cold start 수십 초 |
| **인증** | user_id를 클라이언트가 임의 설정 가능 | 어뷰징 가능, 파트너 인증 없음 |
| **지역 고정** | 파주출판단지 BBox 하드코딩 | 다른 지역/이벤트 확장 불가 |
| **분석** | 어드민 대시보드·분석 파이프라인 없음 | 캠페인 성과 파악 불가 |
| **프론트엔드** | App.jsx 700+ 줄 단일 컴포넌트 | 유지보수·기능 확장 병목 |

---

## 3. 상용화 전략

### 3.1 비즈니스 모델 (B2B2C)

```
[파트너사 (B2B)]                    [방문객 (C)]
  서점 / 카페 / 식당                  스마트폰으로 사진 촬영
  출판단지 운영사                      미션 완료 → 쿠폰 수령
  지자체 관광 캠페인         →         파트너 POS에서 혜택 사용
        ↓
  [PAZULE 플랫폼 (B2B API)]
  캠페인 설계 + 쿠폰 발급 + 리포트
```

### 3.2 수익 모델

| 채널 | 과금 방식 | 비고 |
|---|---|---|
| **성과 수수료** | 쿠폰 사용(redeem) 건당 정액 | 파트너사 부담, 0원 리스크 도입 |
| **플랫폼 구독** | 월정액 (미션 설계 + 어드민 대시보드) | 중소 파트너 대상 |
| **이벤트 패키지** | 단발 캠페인 기획·운영비 | 지자체·대형 이벤트 대상 |
| **데이터 리포트** | 방문 패턴·랜드마크 인기도 분석 | 주기적 PDF/대시보드 제공 |
| **화이트라벨 API** | 타 관광지에 동일 솔루션 라이선스 | 파주 → 인사동·제주·DMZ 등 확장 |

### 3.3 확장 로드맵

```
Phase 1 (3개월) - MVP 프로덕션화
  · JSON → PostgreSQL 마이그레이션
  · 인증 도입 (JWT 또는 익명 세션)
  · Docker 컨테이너화 + 클라우드 배포
  · 파주출판단지 파트너 2–3곳 파일럿

Phase 2 (6개월) - 플랫폼화
  · 어드민 대시보드 (캠페인 관리, 쿠폰 현황, 방문 히트맵)
  · 다중 site 지원 (BBox를 DB에서 관리)
  · 파트너 POS 웹훅 / API 키 관리
  · 모델 서빙 독립화 (Triton Inference Server or 전용 GPU 서버)

Phase 3 (12개월) - 스케일 아웃
  · 지역 확장 (다른 관광 클러스터)
  · 다국어 UI (영·중·일)
  · 오프라인 QR 연동 (GPS 없는 실내 미션)
  · LLM 기반 개인화 힌트 시스템
```

---

## 4. 배포 파이프라인 설계

### 4.1 목표 아키텍처

```
                          ┌─────────────────────────────────────┐
                          │           CDN (CloudFront)           │
                          │     React SPA (S3 or Vercel)         │
                          └─────────────┬───────────────────────┘
                                        │ HTTPS
                          ┌─────────────▼───────────────────────┐
                          │        API Gateway / ALB             │
                          └──┬──────────────────────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  API Server  │  │  API Server  │  │  API Server  │  ← Auto Scaling (CPU 기반)
    │  (FastAPI)   │  │  (FastAPI)   │  │  (FastAPI)   │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │ gRPC / HTTP
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Model Server │  │ Model Server │  │ Model Server │  ← GPU 인스턴스 (고정)
    │ (Triton or   │  │              │  │              │
    │  FastAPI)    │  │              │  │              │
    │ SigLIP2+BLIP │  │   Qwen-VL    │  │  예비/배치   │
    └──────────────┘  └──────────────┘  └──────────────┘
           │
    ┌──────▼──────────────────────────────────────────┐
    │              PostgreSQL (RDS / Supabase)         │
    │  테이블: sessions, coupons, users, sites, events │
    └─────────────────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────────┐
    │              S3 / Object Storage                 │
    │  · 제출 이미지 (임시 저장 → 분석 후 삭제 or 보관) │
    │  · 모델 가중치 캐시                              │
    └─────────────────────────────────────────────────┘
```

### 4.2 서비스 분리 원칙

```
API 서버 (CPU)          : 라우팅, 세션 관리, 쿠폰 발급, 비즈니스 로직
Model 서버 (GPU)        : SigLIP2, BLIP, Qwen-VL 추론 전용
Admin 서버 (CPU)        : 어드민 대시보드 백엔드
LangGraph Orchestrator  : API 서버 내부에서 유지 (상태 머신 경량)
```

### 4.3 DB 스키마 변경

현재 JSON 파일 구조를 아래 테이블로 마이그레이션:

```sql
-- 사이트 (이벤트 지역) 관리
CREATE TABLE sites (
  id          VARCHAR PRIMARY KEY,         -- 'pazule-default', 'insadong-2026' 등
  name        TEXT NOT NULL,
  bbox_min_lat FLOAT NOT NULL,
  bbox_max_lat FLOAT NOT NULL,
  bbox_min_lon FLOAT NOT NULL,
  bbox_max_lon FLOAT NOT NULL,
  active      BOOLEAN DEFAULT TRUE
);

-- 미션 정답 (일별 스케줄)
CREATE TABLE daily_answers (
  site_id       VARCHAR REFERENCES sites(id),
  date          DATE NOT NULL,
  location_answer TEXT,
  location_hint   TEXT,
  atmosphere_answer TEXT,
  atmosphere_hint   TEXT,
  PRIMARY KEY (site_id, date)
);

-- 미션 세션
CREATE TABLE mission_sessions (
  mission_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       VARCHAR NOT NULL,
  site_id       VARCHAR REFERENCES sites(id),
  mission_type  VARCHAR NOT NULL,           -- 'location' | 'atmosphere'
  answer        TEXT,
  hint          TEXT,
  status        VARCHAR DEFAULT 'created',  -- created|submitted|coupon_issued
  max_submissions INT DEFAULT 3,
  expires_at    TIMESTAMPTZ NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 제출 기록
CREATE TABLE submissions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id    UUID REFERENCES mission_sessions(mission_id),
  user_id       VARCHAR NOT NULL,
  image_hash    VARCHAR NOT NULL,
  success       BOOLEAN,
  confidence    FLOAT,
  model_votes   JSONB,
  submitted_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 쿠폰
CREATE TABLE coupons (
  code          VARCHAR PRIMARY KEY,
  mission_id    UUID UNIQUE REFERENCES mission_sessions(mission_id),
  partner_id    VARCHAR,
  discount_rule VARCHAR,
  status        VARCHAR DEFAULT 'issued',  -- issued|redeemed|expired
  issued_at     TIMESTAMPTZ DEFAULT NOW(),
  expires_at    TIMESTAMPTZ,
  redeemed_at   TIMESTAMPTZ,
  partner_pos_id VARCHAR
);
```

### 4.4 CI/CD 파이프라인

```
GitHub Push
    │
    ▼
┌──────────────────────────────────────────────────┐
│                  GitHub Actions                   │
│                                                  │
│  1. Lint + Type Check (ruff, mypy)               │
│  2. Unit Tests (pytest, mock models)             │
│  3. Integration Test (test_pipeline_mock.py)     │
│  4. Docker Build                                 │
│     ├── api-server:  Dockerfile.api              │
│     └── model-server: Dockerfile.model (GPU)    │
│  5. Push to ECR / GHCR                          │
└──────────────────────────────────────────────────┘
    │
    ▼ (main 브랜치 merge 시)
┌──────────────────────────────────────────────────┐
│               Staging 배포 (자동)                 │
│  · ECS Fargate (API) + EC2 GPU (Model)           │
│  · DB 마이그레이션 (Alembic)                     │
│  · E2E 스모크 테스트 (실제 이미지 제출 시나리오)  │
└──────────────────────────────────────────────────┘
    │
    ▼ (수동 승인 후)
┌──────────────────────────────────────────────────┐
│               Production 배포 (Blue/Green)        │
│  · Traffic 전환 (ALB weighted routing)           │
│  · Canary: 10% → 50% → 100%                     │
│  · 롤백 트리거: 에러율 > 1% or P99 > 5s          │
└──────────────────────────────────────────────────┘
```

### 4.5 Docker 구성

```dockerfile
# Dockerfile.api  (CPU, 경량)
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv pip install ".[langraph]" --system
COPY app/ ./app/
COPY data/ ./data/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

# Dockerfile.model  (GPU)
FROM nvidia/cuda:12.1-base-ubuntu22.04
RUN apt-get install -y python3-pip
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv pip install ".[model]" --system
COPY app/models/ ./app/models/
# 모델 가중치는 S3에서 시작 시 다운로드 (콜드 스타트 개선: EFS 마운트 권장)
CMD ["python", "-m", "app.model_server"]
```

### 4.6 환경별 설정 분리

```
environments/
  dev.env       # 로컬 개발 (mock 모델, JSON 파일 DB)
  staging.env   # 스테이징 (실제 모델, RDS staging DB)
  prod.env      # 프로덕션 (실제 모델, RDS prod DB, 엄격한 BBox)
```

```env
# staging.env 예시
DATABASE_URL=postgresql://pazule:***@rds-staging.us-east-1.rds.amazonaws.com/pazule
MODEL_SERVER_URL=http://model-server-internal:8001
MODEL_SELECTION_LOCATION=ensemble
ENSEMBLE_MODELS_LOCATION=siglip2,blip
COUNCIL_ENABLED=true
COUNCIL_BORDERLINE_MARGIN=0.08
LOCATION_PASS_THRESHOLD=0.70
ATMOSPHERE_PASS_THRESHOLD=0.62
```

---

## 5. 단기 필수 개선 과제 (Phase 1 체크리스트)

### 5.1 백엔드 안정화

- [ ] **Flask → FastAPI 전환**: async 지원, 자동 OpenAPI 문서, 더 나은 성능
- [ ] **JSON → PostgreSQL**: `MissionSessionService` + `CouponService`의 `_read_all`/`_write_all`을 ORM으로 교체
- [ ] **이미지 임시 파일**: tempfile → S3 presigned URL 업로드로 변경 (서버 디스크 의존 제거)
- [ ] **모델 서버 분리**: `evaluator` 노드가 HTTP 콜로 외부 모델 서버를 호출하도록 `ModelRegistry` 수정
- [ ] **인증 레이어**: `user_id` 클라이언트 신뢰 제거 → JWT 발급 or 익명 토큰

### 5.2 어뷰징 방어 강화

- [ ] GPS EXIF 우회 방지: 클라이언트에서도 Geolocation API로 이중 검증 (선택)
- [ ] IP Rate Limiting (Redis + Flask-Limiter)
- [ ] 쿠폰 재발급 요청 어뷰징 방지 (mission_id 기반 멱등은 이미 구현됨)

### 5.3 관찰성 (Observability)

- [ ] 구조화된 로그: `logging` → JSON 구조화 (Datadog / CloudWatch Logs Insights)
- [ ] 메트릭: Prometheus + Grafana
  - 미션 통과율 per mission_type
  - 모델별 평균 confidence score
  - Council escalation 비율 (Tier 1→2→3)
  - 쿠폰 발급/사용 conversion rate
- [ ] 분산 추적: OpenTelemetry (LangGraph 노드별 span)
- [ ] 알림: 에러율 급증, GPU 메모리 OOM

### 5.4 프론트엔드 개선

- [ ] `App.jsx` 700줄 → 컴포넌트 분리 (`MissionFlow`, `CouponResult`, `HintDisplay`)
- [ ] PWA 지원 (오프라인 캐시, 홈 화면 추가)
- [ ] 모바일 카메라 직접 촬영 UX 최적화
- [ ] i18n 기반 준비 (한/영 최소 지원)

---

## 6. 모델 서빙 전략

### 6.1 모델 계층 분리

```
┌──────────────────────────────────────────────────────────┐
│  Light Models (SigLIP2, BLIP) — 모든 요청에 실행         │
│  GPU A10G 1장, 배치 크기 1–4, 응답 < 2초                │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│  Heavy Model (Qwen-VL 8B) — borderline일 때만 호출       │
│  GPU A100 1장, 배치 크기 1, 응답 < 10초                  │
│  예상 투입 비율: 전체 요청의 ~15%                        │
└──────────────────────────────────────────────────────────┘
```

### 6.2 비용 최적화

| 전략 | 방법 |
|---|---|
| Qwen 호출 억제 | Council Tier 3 투입 임계값 조정 (현재 ±0.08 margin) |
| 모델 캐싱 | SigLIP2/BLIP 가중치 EFS 마운트로 cold start 0초 |
| Spot 인스턴스 | GPU 모델 서버를 EC2 Spot으로 실행 (비용 70% 절감, 내결함성 처리 필요) |
| 비동기 큐 | 트래픽 피크 시 SQS → Worker 구조로 전환 |

---

## 7. 파트너 통합 설계

### 7.1 파트너 어드민 API

```
POST /partner/api-key          # API 키 발급
GET  /partner/campaigns        # 내 캠페인 목록
POST /partner/campaigns        # 캠페인 생성 (site_id, 기간, 미션 설정)
GET  /partner/coupons/stats    # 쿠폰 발급/사용 통계
GET  /partner/coupons          # 쿠폰 목록 + 상태 조회
```

### 7.2 POS 연동 방식

```
Option A (현재): POST /api/coupon/redeem + partner_pos_id
Option B (권장): POS QR Scanner → PAZULE API 직접 호출
Option C (고급): 파트너 POS 시스템 웹훅 (redemption 이벤트 push)
```

### 7.3 쿠폰 정책 커스터마이징

현재 하드코딩된 `discount_rule: "10%_OFF"` 를 DB 캠페인 테이블로 이동:
```json
{
  "campaign_id": "paju-spring-2026",
  "partner_id": "partner-bookstore-01",
  "discount_rule": "BOOK_500WON_OFF",
  "coupon_expires_days": 14,
  "max_issuance_per_user": 1
}
```

---

## 8. 보안 고려사항

| 위험 | 현재 상태 | 대응 |
|---|---|---|
| GPS 조작 | EXIF 검증만 (소프트웨어 조작 가능) | 추가: 서버 측 Geolocation 더블체크 옵션 |
| 사진 재사용 | SHA-256 유저별 해시 중복 체크 ✓ | perceptual hash 추가로 약간 수정 사진도 탐지 |
| 쿠폰 코드 브루트포스 | 8자리 알파뉴메릭 (36^8 ≈ 28억) | HMAC 서명 포함 코드로 교체 권장 |
| user_id 위조 | 클라이언트 임의 설정 가능 | JWT 서명 필수화 |
| 이미지 저장 | 임시파일 서버 디스크 | S3 전환 + 분석 후 자동 삭제 |
| API 인증 | 없음 | API Key (파트너) + JWT (사용자) |

---

## 9. 성공 지표 (KPI)

```
사용자 경험
  · 미션 완료율        ≥ 40% (제출자 기준)
  · 쿠폰 사용률        ≥ 25% (발급 기준)
  · 미션 응답 P99      ≤ 5초

기술 품질
  · 위치 미션 정확도   ≥ 90% (오탐·미탐 합산)
  · 감성 미션 정확도   ≥ 80%
  · Council 에스컬레이션 ≤ 20% (Tier 3 Qwen 투입 비율)
  · API 가용성         ≥ 99.5%

비즈니스
  · 파트너 계약 수     Phase 1: 3+, Phase 2: 10+
  · 쿠폰 전환 매출     파트너사 증분 매출 기준 ROI 측정
```

---

## 10. 즉시 실행 가능한 Quick Wins

1. **DB 전환** — `MissionSessionService` + `CouponService`의 파일 I/O를 SQLAlchemy ORM으로 교체 (구조는 이미 클래스 기반이라 인터페이스 변경 최소)
2. **Flask → FastAPI** — Blueprint 구조를 FastAPI Router로 1:1 포팅, async 지원으로 모델 서버 HTTP 호출 비차단화
3. **Docker Compose 로컬 환경 표준화** — `docker-compose.yml`: api, model-server, postgres 3-컨테이너 구성
4. **모델 서버 분리 준비** — `ModelRegistry`에 HTTP adapter 추가, 환경변수로 local/remote 전환
5. **Github Actions CI** — `pytest` + `ruff` lint 자동 실행 (현재 없음)
