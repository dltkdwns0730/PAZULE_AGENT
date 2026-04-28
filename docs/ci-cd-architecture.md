# CI/CD Architecture

이 문서는 현재 저장소에 있는 CI/CD 구성만 설명합니다. 실행 이력이나 버전별 구축 과정은 다루지 않습니다.

## Current Files

| 파일 | 역할 |
|---|---|
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | push/PR 코드 검사와 pytest 실행 |
| [.github/workflows/cd.yml](../.github/workflows/cd.yml) | Docker image build와 ghcr.io publish |
| [Dockerfile](../Dockerfile) | uv 기반 Python 3.12 multi-stage backend image |
| [.pre-commit-config.yaml](../.pre-commit-config.yaml) | local ruff/ruff-format hook |

## CI

```text
push or pull_request
  -> checkout
  -> setup uv
  -> uv python install 3.12
  -> uv sync --dev
  -> uv run ruff check .
  -> uv run pytest
```

CI는 백엔드 Python 품질 게이트입니다. 프론트엔드 `npm run build`, `npm run lint`, `npm test`는 현재 로컬 검증 명령으로 README와 테스트 문서에 명시되어 있습니다.

## CD

```text
main branch push
  -> Docker Buildx
  -> ghcr.io login
  -> docker metadata
  -> docker build and push
```

Dockerfile은 `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` builder와 `python:3.12-slim-bookworm` runtime image를 사용합니다.

## Local Quality Gate

`.pre-commit-config.yaml`은 ruff와 ruff-format hook을 사용합니다.

```bash
uv run ruff check .
uv run pytest
```

프론트엔드 검증은 `front/`에서 별도로 실행합니다.

```bash
cd front
npm run build
npm run lint
npm test
```

## Deployment Notes

- 패키징 대상은 백엔드 Docker image입니다.
- image registry는 `ghcr.io/${{ github.repository }}`입니다.
- 운영 환경 변수와 Supabase 연결 값은 image 내부에 고정하지 않고 배포 환경에서 주입합니다.
