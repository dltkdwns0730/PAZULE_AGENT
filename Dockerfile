# 1. Builder Stage: uv를 사용한 초고속 패키지 설치
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app
# 의존성 파일만 먼저 복사하여 캐시를 극대화
COPY pyproject.toml uv.lock ./

# 프로덕션 배포용이므로 --no-dev 로 운영에 필요한 패키지만 설치
RUN uv sync --frozen --no-install-project --no-dev

# 전체 앱 소스코드 복사 후 패키지 설치 확정
COPY . /app
RUN uv sync --frozen --no-dev

# 2. Production Stage: 실행 전용 가벼운 이미지
FROM python:3.12-slim-bookworm

WORKDIR /app
# Builder 단계에서 의존성과 코드가 설치된 .venv를 통째로 복사해옵니다. 
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# 보안: root 권한 방지를 위해 최소 권한의 새 유저 생성 및 전환
RUN useradd -m appuser
USER appuser

# Flask나 FastAPI 서버 실행 (현재 프로젝트에서는 python main.py 로 가정)
CMD ["python", "main.py"]
