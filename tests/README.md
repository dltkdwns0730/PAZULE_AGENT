# tests/ Test Guide

`tests/`는 PAZULE 백엔드의 pytest 테스트를 담습니다. 프론트엔드 테스트는 `front/src/test/`에서 Vitest로 실행합니다.

## Scope

| 위치 | 대상 |
|---|---|
| `tests/api/` | Flask route, 인증, 관리자 API |
| `tests/core/` | 설정, 상수, 힌트/분위기 로직 |
| `tests/council/` | LangGraph 노드, 집계, council 판정 |
| `tests/db/` | SQLAlchemy session, repository, DB 저장소 경계 |
| `tests/models/` | AI model adapter와 prompt/model registry |
| `tests/services/` | 정답, 쿠폰, 위치, 미션 세션 서비스 |
| `tests/legacy/` | 호환 코드 동작 보존 |
| `front/src/test/` | React hook, page, service 단위 테스트 |

## Commands

```bash
# Backend
uv run pytest
uv run pytest tests/api/test_routes.py tests/api/test_admin_routes.py
uv run pytest --cov=app --cov-report=term-missing

# Frontend
cd front
npm test
npm run build
npm run lint
```

## Coverage Settings

커버리지 기준은 [pyproject.toml](../pyproject.toml)의 `[tool.coverage]` 설정을 기준으로 합니다.

| 항목 | 현재 설정 |
|---|---|
| coverage source | `app` |
| fail under | `80` |
| omitted paths | `app/legacy/*`, `app/__main__.py`, `*/__init__.py` 등 설정 파일 기준 |

정확한 테스트 개수와 통과 수는 고정 문서값이 아니라 테스트 러너 출력이 기준입니다. 테스트가 추가되거나 분리될 때 문서의 숫자를 수동 갱신하지 않고, 필요한 경우 실행 결과를 task 문서에 기록합니다.

## Test Writing Rules

- 정상 입력, 누락 입력, 예외, 경계값을 분리해서 검증합니다.
- 외부 API, AI 모델, 파일/DB I/O는 mock 또는 임시 저장소를 사용합니다.
- 인증 경계는 Supabase JWT claim과 서버가 검증한 `sub`를 기준으로 테스트합니다.
- 기업 관리자 테스트는 `platform_master`와 기업 소속 관리자 스코프를 분리해 검증합니다.
- 새 route를 추가하면 `tests/api/`에 HTTP 상태 코드와 응답 shape 테스트를 추가합니다.
