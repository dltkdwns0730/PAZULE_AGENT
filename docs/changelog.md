# PAZULE Changelog

> **분류**: 레퍼런스 · **버전**: v2.5.0 · **최종 수정**: 2026-04-14
>
> 프로젝트의 주요 변경 이력을 버전별로 정리합니다.

---

## v1.0 — 수상작 (파주시장상)

> 레포: [`PAZULE`](https://github.com/dltkdwns0730/PAZULE) / 팀 프로젝트

- **모델**: BLIP-VQA (장소 검증) + CLIP (분위기 판별) + GPT-4o-mini (힌트 생성)
- **구조**: `mission_manager.py` → `run_blip()` → `run_clip()` → `generate_hint()` 직렬 호출
- **API**: `POST /mission` 단일 엔드포인트
- **데이터**: `landmark_qa_labeled.json` (10개 랜드마크, 각 40개 QA), `answer.json` (일별 정답)
- **프론트엔드**: 없음 (CLI 기반)
- **한계**:
  - 단일 모델 오탐 보정 수단 없음
  - 미션 상태 비관리 (같은 사진 반복 제출 가능)
  - CLIP이 무거워 로컬 환경에서 응답 시간/메모리 부담

---

## v2.0 — 개인 고도화

> 레포: [`PAZULE_AGENT`](https://github.com/dltkdwns0730/PAZULE_AGENT) / 개인

### v2.0.0 — 프로젝트 재설계 (PR #1 ~ #6)

- `feat(core)`: Settings 설정 + 감성 키워드 매핑
- `feat(data)`: 미션 정답/랜드마크 QA 데이터셋
- `feat(metadata)`: EXIF/GPS 추출 + BBox 유효성 검증
- `feat(models)`: BLIP-VQA 모듈 + LLM 힌트/감성 서비스
- `feat(services)`: 정답 관리, 쿠폰 발급, 미션 실행 서비스
- `feat(council)`: LangGraph Council 아키텍처 도입

### v2.1.0 — API + CLI + Frontend (PR #7 ~ #9)

- `feat(api)`: Flask Blueprint 엔드포인트 (`/api/mission/start`, `/submit`, `/coupon/issue`, `/redeem`)
- `feat(cli)`: 터미널 기반 게임 루프 (`scripts/simulate_cli.py`)
- `feat(front)`: React 19 + Vite SPA (인트로 → 미션 선택 → 업로드 → 결과 → 쿠폰)

### v2.2.0 — 멀티모델 + 앙상블 (PR #10 ~ #11)

- `feat(models)`: SigLIP2 · Qwen VL 어댑터 추가
- SigLIP2로 CLIP 대체 (가볍고 빠른 zero-shot 매칭)
- Qwen VL은 OpenRouter API로 호출 (로컬 부담 제거)
- 모델 레지스트리 패턴 도입 (`ModelRegistry`)

### v2.3.0 — 파이프라인 통합 + UI 개선 (PR #12 ~ #22)

- `feat(council)`: 3-Tier 에스컬레이션 (ConsistencyJudge → ThresholdJudge → QwenFallbackJudge)
- `refactor(council)`: Upstage → OpenRouter 전환
- `refactor(front)`: Clean White/Coral 테마, 하단 네비게이션 4탭 개편
- 쿠폰 멱등성 (`mission_id` 기반 중복 발급 방지)
- 세션 생애주기 관리 (TTL, 최대 제출 횟수, 이미지 해시 중복 차단)

### v2.4.0 — 문서화 + 상용화 전략

- `docs/architecture.md`: 하네스 설계, 상태 흐름, Council 에스컬레이션 상세
- `docs/commercialization-plan.md`: 프로덕션 전환 설계
- `docs/benchmarks/`: SigLIP2 성능 벤치마크 시작

### v2.4.1 — TDD 기반 프론트엔드 버그 수정 (2026-04-14)

> 브랜치: `fix/front-tdd-api-hooks-photo-bugs` → main 병합 완료
> 상세 원인·수정·검증 이력: [`docs/bugfix-log.md`](./bugfix-log.md)

- `chore(test-env)`: Vitest + Testing Library 테스트 환경 초기 구성 (`0ed9608`)
  - Jest 대신 Vitest 선택 — Vite 스택 네이티브, ES Module 지원, Babel 불필요
- `fix(api)` — **BUG-001**: 모든 fetch 호출에 `fetchWithTimeout()` 헬퍼 적용, 10초 초과 시 AbortController로 자동 취소 (`01f52cb`)
- `fix(hooks)` — **BUG-002**: `fetchHint()`에 `setIsLoading(true/false)` 추가, 힌트 로딩 중 스피너 미표시 수정 (`3165017`)
- `fix(pages)` — **BUG-003**: `PhotoSubmission.jsx` stale state race condition 수정, `newAttemptsLeft` 지역 변수로 navigate 조건 확정 (`f69d982`)
- `fix(pages)` — **BUG-004**: `missionId` 없이 `/mission/submit` 직접 접근 시 `'/'`로 redirect하는 route guard 추가 (`f69d982`)

---

## v2.5.0 — CI/CD 자동화 파이프라인 구축 (2026-04-14)

> 학습 목적의 클라우드 독립형(Cloud-less) 파이프라인. 로컬 훅부터 GitHub Actions까지 uv 100% 활용.

- `feat(ci)`: `pyproject.toml` dev 의존성에 `ruff`, `pre-commit` 추가
- `feat(ci)`: `.pre-commit-config.yaml` 훅 추가 (코드 커밋 전 ruff 검사 강제화)
- `feat(ci)`: `.github/workflows/ci.yml` 구축 (uv 기반 초고속 테스트 및 린트 파이프라인)
- `feat(cd)`: 멀티스테이지 `Dockerfile` 작성 (uv builder 활용 경량 이미지)
- `feat(cd)`: `.github/workflows/cd.yml` 패키징 구축 (ghcr.io 자동 배포)
- `docs(architecture)`: `ci-cd-architecture.md` 명세서 작성
