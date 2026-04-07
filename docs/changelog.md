# PAZULE Changelog

> **분류**: 레퍼런스 · **버전**: v2.4 · **최종 수정**: 2026-04-07
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

### v2.4.0 — 문서화 + 상용화 전략 (현재)

- `docs/architecture.md`: 하네스 설계, 상태 흐름, Council 에스컬레이션 상세
- `docs/commercialization-plan.md`: 프로덕션 전환 설계
- `docs/benchmarks/`: SigLIP2 성능 벤치마크 시작
