# PAZULE

위치 기반 AI 미션 인증과 쿠폰 발급을 연결하는 B2B2C 미션 플랫폼입니다.

[![Python](https://img.shields.io/badge/Python-%3E%3D3.10-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-%3E%3D2.3-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-7-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vite.dev)
[![CI/CD](https://github.com/dltkdwns0730/PAZULE_AGENT/actions/workflows/ci.yml/badge.svg)](https://github.com/dltkdwns0730/PAZULE_AGENT/actions)

PAZULE은 방문자가 실제 장소에서 사진 미션을 수행하면 GPS, EXIF, 이미지 해시, AI 판정을 거쳐 쿠폰을 발급합니다. 관리자 콘솔은 기업별 미션 로그, 쿠폰, 사용자 활동을 분리해 조회하고, 플랫폼 마스터는 전체 기업 데이터를 추적할 수 있습니다.

## At A Glance

| 대상 | 먼저 확인할 내용 |
|---|---|
| 일반 사용자 | Google OAuth로 로그인하고 오늘의 힌트를 확인한 뒤, 현장에서 사진을 제출해 쿠폰을 받습니다. |
| 기업/파트너 | 기업별 미션 로그, 쿠폰 발급/사용 상태, 사용자 활동을 관리자 콘솔에서 확인합니다. |
| 면접관/리뷰어 | LangGraph 파이프라인, Supabase Auth/DB 경계, 테스트/CI 기반 운영 구조를 확인할 수 있습니다. |

## Current Capabilities

- 사용자 인증: Supabase OAuth/JWT 기반 로그인과 사용자 소유 미션 세션 검증.
- 미션 검증: GPS 반경, EXIF, 이미지 해시, SigLIP2/BLIP/Qwen VL 기반 AI 판정.
- 쿠폰 운영: 미션 성공 시 쿠폰 발급, 지갑 조회, 관리자 콘솔 리딤 처리.
- 기업 스코프: `organizations -> sites -> mission_sessions` 구조로 기업별 운영 데이터 분리.
- 관리자 권한: `platform_master`는 전체 조회, 기업 관리자는 소속 기업 데이터 조회.
- 운영 문서: 계정 분류, 설정, 아키텍처, CI/CD, 상용화 검토 문서를 `docs/`에 분리.

## Architecture Snapshot

```text
React SPA
  -> Flask API
  -> Supabase JWT / GPS / EXIF / hash validation
  -> LangGraph AI mission pipeline
  -> mission session and coupon storage
  -> admin console scoped by organization
```

현재 백엔드 API는 [app/api/routes.py](./app/api/routes.py)에 16개 Flask route로 정의되어 있습니다. 프론트엔드 관리자 화면은 `/admin`, `/admin/logs`, `/admin/logs/:missionId`, `/admin/coupons`, `/admin/users` 경로를 사용합니다.

## Tech Stack

| 영역 | 기술 |
|---|---|
| Backend | Python `>=3.10`, Flask `>=2.3`, SQLAlchemy, Alembic |
| Frontend | React 19, Vite 7, React Router, Zustand, Tailwind CSS |
| AI/ML | LangGraph, SigLIP2, BLIP, Qwen VL, OpenAI/OpenRouter/Gemini 연동 |
| Auth/DB | Supabase Auth, Supabase Postgres, JWT 검증 |
| DevOps/Test | uv, pytest, ruff, Vitest, ESLint, GitHub Actions, Docker |

## Run Locally

The default development profile is clone-and-run friendly: JSON storage, demo auth,
metadata skip, and model bypass are enabled so reviewers can inspect the core flow
without private `.env` secrets.

### Backend Virtual Environment

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

If the virtual environment already exists, start from the activation command.
`uv run ...` can also run commands without manual activation, but activation makes
the selected Python environment explicit while working in the terminal.

### Frontend

```bash
cd front
npm install
npm run dev
```

기본 포트는 백엔드 `8080`, 프론트엔드 `5173`입니다. 환경 변수와 기본값은 [app/core/config/README.md](./app/core/config/README.md)를 기준으로 확인합니다.

## Demo Mode

| 항목 | 동작 |
|---|---|
| 사용자 데모 | 로그인 화면의 `사용자 데모` 버튼으로 미션/쿠폰 흐름 확인 |
| 관리자 데모 | 로그인 화면의 `관리자 데모` 버튼으로 `/admin` 콘솔 확인 |
| 백엔드 인증 | `DEMO_AUTH_ENABLED=true`에서 `demo-user-token`, `demo-admin-token` 허용 |
| 저장소 | `STORAGE_BACKEND=json`으로 로컬 `data/` 파일 사용 |
| AI/메타데이터 | development 기본값에서 `BYPASS_MODEL_VALIDATION=true`, `SKIP_METADATA_VALIDATION=true` |

Demo mode is intended for checking the product flow only. When
`BYPASS_MODEL_VALIDATION=true`, the backend skips real SigLIP2/BLIP/Qwen model
inference and uses the demo bypass decision path instead. Demo pass rates,
`confidence`, and `model_votes` must not be interpreted as AI model accuracy
metrics. Validate real model behavior with `BYPASS_MODEL_VALIDATION=false` and
the required API keys or local model environment configured.

실서비스 방식으로 실행하려면 `.env.example`을 참고해 Supabase와 AI provider 값을 채우고 `PAZULE_ENV=production`, `DEMO_AUTH_ENABLED=false`, `STORAGE_BACKEND=db`를 사용합니다.

## Verification

```bash
uv run pytest
uv run ruff check .

cd front
npm run build
npm run lint
npm test
```

테스트 실행 기준과 커버리지 설정은 [tests/README.md](./tests/README.md)에 정리되어 있습니다.

## Project Structure

| 경로 | 역할 |
|---|---|
| [app/](./app/README.md) | Flask API, LangGraph 파이프라인, 서비스, DB/Auth 경계 |
| [front/](./front/) | React 사용자 앱과 관리자 콘솔 |
| [tests/](./tests/README.md) | pytest 백엔드 테스트와 테스트 작성 기준 |
| [scripts/](./scripts/README.md) | Supabase 검증, 벤치마크, 운영 보조 스크립트 |
| [docs/](./docs/README.md) | 현재 상태 기준 설계, 운영, 상용화, 작업 기록 문서 |

## Docs Map

| 문서 | 내용 |
|---|---|
| [Architecture](./docs/architecture.md) | LangGraph 파이프라인과 현재 시스템 구조 |
| [Admin Company Account Classification](./docs/admin-company-account-classification.md) | 기업별 관리자 계정 분류와 Supabase SQL 작업 절차 |
| [Commercialization Plan](./docs/commercialization-plan.md) | 현재 제품 구조 기준 B2B2C 상용화 검토 |
| [CI/CD Pipeline](./docs/ci-cd-architecture.md) | GitHub Actions, Docker, ghcr.io 패키징 구조 |
| [Task Index](./docs/TASK_INDEX.md) | 작업 문서 인덱스 |
| [Documentation Guide](./docs/doc-guide.md) | 문서 작성 규칙 |

## Project Status

- 사용자 미션은 Supabase OAuth 인증 후 서버가 검증한 사용자 ID를 기준으로 소유권을 관리합니다.
- 운영 데이터는 기업 단위로 분리되며, 플랫폼 마스터는 전체 기업을 조회할 수 있습니다.
- 쿠폰과 미션 세션은 `STORAGE_BACKEND` 설정에 따라 JSON 또는 DB 저장소 경계를 사용합니다.
- 현재 설정 기본값은 위치 임계값 `0.70`, 분위기 임계값 `0.35`, 세션 TTL `60`분, 최대 제출 `3`회, 위치 반경 `300m`입니다.
