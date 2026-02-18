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
- Recommended models: `blip`, `qwen`, `clip`
- Default ensemble weights:
  - `blip`: `0.45`
  - `qwen`: `0.35`
  - `clip`: `0.20`

### 2) Atmosphere Mission
- Goal: verify whether the uploaded image matches the target atmosphere keyword
- Recommended models: `siglip2`, `qwen`, `blip`, `clip`
- Default ensemble weights:
  - `siglip2`: `0.45`
  - `qwen`: `0.35`
  - `blip`: `0.15`
  - `clip`: `0.05`

## Orchestration Pipeline

Entrypoint: `app/council/graph.py` -> `pipeline_app`

```text
START
  -> gate_keeper
      pass -> task_router
      fail -> finalizer(error)
  -> task_router
  -> model_fanout
  -> evidence_aggregator
  -> decision_engine
      success -> coupon_policy_engine
      fail    -> finalizer(fail)
  -> coupon_policy_engine
  -> finalizer(success)
END
```

## Node Responsibilities

- `gate_keeper` (`app/council/nodes.py`)
  - validates metadata
  - checks duplicate image hash per user
  - writes `gate_result` and risk flags

- `task_router`
  - normalizes mission type (`photo` -> `atmosphere`)
  - writes route decision metadata

- `model_fanout`
  - selects single model or ensemble from config/runtime override
  - runs model probes and collects `model_votes`

- `evidence_aggregator`
  - merges votes with mission-specific weights
  - computes `merged_score`, `threshold`, and `conflict`

- `decision_engine`
  - applies pass/fail threshold
  - applies conservative handling when conflict is high

- `coupon_policy_engine`
  - converts mission judgment to coupon eligibility policy

- `finalizer`
  - builds API response DTO (`success`, `message`, `confidence`, traces)

## API Surface

See full schema and examples in `API_SPEC.md`.

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
ENSEMBLE_MODELS_LOCATION=blip,qwen,clip
ENSEMBLE_MODELS_ATMOSPHERE=siglip2,qwen,blip,clip
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
    blip.py
    clip.py
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
```

## Run Locally

```bash
cd projects/active/PAZULE
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
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
