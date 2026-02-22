# PAZULE

PAZULE is an AI mission platform that verifies **location** and **atmosphere** missions from uploaded photos, then issues redeemable coupons for successful missions.

This repository now uses a LangGraph-based orchestration pipeline with mission session lifecycle control and coupon lifecycle control.

## What This Build Delivers

- Mission session lifecycle (`start -> submit -> issue -> redeem`)
- Image gate checks (metadata validation, duplicate image prevention)
- Model orchestration with fan-out/fan-in and weighted decision
- Mission-type aware model routing (`location`, `atmosphere`)
- Coupon issuance idempotency per mission
- Coupon redeem state transitions (`issued -> redeemed|expired`)

## Mission Types and Model Strategy

### 1) Location Mission
- Goal: verify whether the uploaded image matches the target place
- Recommended models: `siglip2`, `blip`, `qwen`
- Default ensemble weights:
  - `siglip2`: `0.50`
  - `blip`: `0.30`
  - `qwen`: `0.20`

### 2) Atmosphere Mission
- Goal: verify whether the uploaded image matches the target atmosphere keyword
- Recommended models: `siglip2`, `qwen`, `blip`
- Default ensemble weights:
  - `siglip2`: `0.60`
  - `qwen`: `0.25`
  - `blip`: `0.15`

## Orchestration Pipeline

Entrypoint: `app/council/graph.py` -> `pipeline_app`

```text
START
  -> validator
      pass -> router
      fail -> responder(error)
  -> router
  -> evaluator
  -> aggregator
  -> council
  -> judge
      success -> policy
      fail    -> responder(fail)
  -> policy
  -> responder(success)
END
```

## Node Responsibilities

- `validator` (`app/council/nodes.py`)
  - validates metadata
  - checks duplicate image hash per user
  - writes `gate_result` and risk flags

- `router`
  - normalizes mission type (`photo` -> `atmosphere`)
  - writes route decision metadata

- `evaluator`
  - selects single model or ensemble from config/runtime override
  - runs model probes and collects `model_votes`

- `aggregator`
  - merges votes with mission-specific weights
  - computes `merged_score`, `threshold`, and `conflict`

- `council`
  - runs final deliberation logic before pass/fail determination (AI Council)

- `judge`
  - applies pass/fail threshold
  - applies conservative handling when conflict is high

- `policy`
  - converts mission judgment to coupon eligibility policy

- `responder`
  - builds API response DTO (`success`, `message`, `confidence`, traces)

## API Surface

See full schema and examples in `docs/api_specification.md`.

- `POST /api/mission/start`
- `POST /api/mission/submit`
- `POST /api/coupon/issue`
- `POST /api/coupon/redeem`
- `GET /get-today-hint`
- `POST /api/preview`

## Business Flow (Location + Atmosphere + Coupon)

1. User starts a mission in a constrained site context (`site_id`, radius policy)
2. User submits an image inside mission TTL and submission limit
3. Pipeline validates trust signals and runs mission-specific model voting
4. If mission succeeds and policy allows it, user receives one coupon
5. Partner POS redeems coupon with audit-ready state transition

This design supports campaign monetization by:
- improving mission quality with multi-model voting
- reducing abuse through duplicate and policy checks
- enabling partner-side redemption tracking

## Configuration

Main config: `app/core/config.py`

Key environment variables:

```env
OPENAI_API_KEY=...
MODEL_SELECTION_LOCATION=blip
MODEL_SELECTION_ATMOSPHERE=ensemble
ENSEMBLE_MODELS_LOCATION=siglip2,blip,qwen
ENSEMBLE_MODELS_ATMOSPHERE=siglip2,qwen,blip
LOCATION_PASS_THRESHOLD=0.70
ATMOSPHERE_PASS_THRESHOLD=0.62
MISSION_SESSION_TTL_MINUTES=60
MISSION_MAX_SUBMISSIONS=3
MISSION_SITE_RADIUS_METERS=300
```

## Project Structure

```text
app/
  api/
    routes.py
  council/
    graph.py
    nodes.py
    state.py
    agents.py
  models/
    qwen_vl.py
    siglip2.py
    prompts.py
    adapter_utils.py
    llm.py
  services/
    mission_session_service.py
    coupon_service.py
    answer_service.py
  core/
    config.py
    keyword.py
  metadata/
    validator.py
    metadata.py

tests/
  test_nodes_logic.py
  test_coupon_service.py

docs/
  api_specification.md
  assets/
    pipeline_architecture.png

scripts/
  simulate_cli.py
  test_real_models.py
  test_pipeline_mock.py
```

## Run Locally

```bash
cd projects/active/PAZULE
python -m venv .venv
.venv\Scripts\activate
```

### Install with uv (Recommended)

API-only runtime:

```bash
uv pip install .
```

Model runtime (BLIP/Qwen/SigLIP2/LangGraph path):

```bash
uv pip install ".[model]"
```

Full local development profile:

```bash
uv pip install ".[dev,model]"
```

### Legacy pip Compatibility

(Legacy requirements.txt was removed, use uv instead)

### 로컬 통합 테스트 (백엔드 + 프론트엔드)

두 서버를 **별도 터미널**에서 동시에 실행합니다:

| 터미널 | 명령어 | URL |
| --- | --- | --- |
| 백엔드 | `python main.py` | `http://localhost:8080` |
| 프론트엔드 | `cd front && npm run dev` | `http://localhost:5173` |

**백엔드 서버 실행:**

```bash
# Windows 콘솔에서 UTF-8 출력이 깨질 경우 먼저 실행
$env:PYTHONUTF8="1"   # PowerShell
set PYTHONUTF8=1      # CMD

python main.py
# → PAZULE vX.X.X 서버 실행 중 (포트 8080)...
```

**프론트엔드 서버 실행:**

```bash
cd front
npm install     # 최초 1회
npm run dev
# → Local: http://localhost:5173
```

브라우저에서 `http://localhost:5173` 접속 시 프론트가 `/api/*` 요청을 백엔드(8080)로 자동 프록시합니다.

### API 엔드포인트 단독 테스트

```bash
# 오늘의 힌트 조회
curl "http://localhost:8080/get-today-hint?mission_type=location"

# 미션 세션 시작
curl -X POST http://localhost:8080/api/mission/start \
  -H 'Content-Type: application/json' \
  -d '{"mission_type": "location", "user_id": "dev-user", "site_id": "pazule-default"}'

# 이미지 제출 (미션 ID는 위 응답의 mission_id 사용)
curl -X POST http://localhost:8080/api/mission/submit \
  -F "mission_id=<mission_id>" \
  -F "image=@/path/to/photo.jpg"
```

### 파이프라인 직접 실행 (Python)

`pipeline_app.invoke()` 를 스크립트에서 바로 호출할 수 있습니다:

```python
from app.council.graph import pipeline_app

initial_state = {
    "request_context": {
        "mission_id":      "test-session-001",   # 임의 세션 ID
        "user_id":         "dev-user",
        "site_id":         "pazule-default",
        "mission_type":    "location",            # "location" | "atmosphere"
        "image_path":      "/path/to/photo.jpg",  # 절대 경로 권장
        "answer":          "한길책박물관",           # 오늘의 정답 키워드
        "model_selection": None,                  # None → .env 기본값 사용
    },
    "artifacts":     {},
    "errors":        [],
    "control_flags": {},
    "messages":      [],
}

output = pipeline_app.invoke(initial_state)

# 최종 판정 결과
final = output.get("final_response", {}).get("data", {})
print(final)
# → {
#     "success":        True,
#     "score":          0.87,
#     "message":        "위치가 확인되었습니다.",
#     "couponEligible": True,
#     "mission_id":     "test-session-001",
#   }
```

보조 스크립트:

```bash
uv run scripts/simulate_cli.py       # 대화형 CLI 시뮬레이션
uv run scripts/test_real_models.py   # 실제 모델 성능 측정
uv run scripts/test_pipeline_mock.py # 목 데이터로 파이프라인 검증
```

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Breaking Changes

- Legacy single endpoint `POST /api/mission` is replaced by:
  - `POST /api/mission/start`
  - `POST /api/mission/submit`
  - `POST /api/coupon/issue`
  - `POST /api/coupon/redeem`
- Frontend clients must follow the new lifecycle sequence.
