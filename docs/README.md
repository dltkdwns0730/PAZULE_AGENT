# docs/ Documentation Map

`docs/`는 PAZULE의 현재 구조, 운영 절차, 검증 기록을 분리해 관리합니다. 루트 README에는 필수 문서만 연결하고, 세부 작업 기록은 `TASK_INDEX.md`에서 추적합니다.

## Current-State Documents

| 문서 | 대상 | 내용 |
|---|---|---|
| [architecture.md](./architecture.md) | 개발자/리뷰어 | 현재 LangGraph 파이프라인, API, 인증, 저장소 구조 |
| [commercialization-plan.md](./commercialization-plan.md) | 기획/리더 | 현재 제품 구조 기준 B2B2C 상용화 검토 |
| [ci-cd-architecture.md](./ci-cd-architecture.md) | 개발자/DevOps | 현재 GitHub Actions, Docker, ghcr.io 패키징 구조 |
| [admin-company-account-classification.md](./admin-company-account-classification.md) | 운영자/관리자 | 기업별 계정 분류, Supabase SQL 작업, 검증 쿼리 |
| [doc-guide.md](./doc-guide.md) | 문서 작성자 | 문서 작성 규칙과 템플릿 기준 |
| [TASK_INDEX.md](./TASK_INDEX.md) | 개발자/PM | 작업 문서 인덱스 |

## Reference and Archive Documents

| 문서 | 용도 |
|---|---|
| [changelog.md](./changelog.md) | 변경 이력 확인용 보관 문서 |
| [bugfix-log.md](./bugfix-log.md) | 버그 수정 상세 이력 확인용 보관 문서 |
| [refactor-audit.md](./refactor-audit.md) | 리팩터링 감사 및 구조 점검 참고 문서 |
| [benchmarks/](./benchmarks/) | AI 모델 벤치마크 템플릿과 측정 보고서 |
| [tasks/](./tasks/) | 날짜별 작업 명세와 검증 기록 |

현재 상태를 설명하는 문서에는 오래된 버전 전환 과정 대신 코드와 설정에서 확인 가능한 값만 적습니다. 변경 이력이 필요하면 `TASK_INDEX.md`, `changelog.md`, `bugfix-log.md`처럼 목적이 명확한 보관 문서에서 확인합니다.

## Update Rules

- 아키텍처, API, 인증, 저장소 경계가 바뀌면 `architecture.md`, 루트 `README.md`, 관련 패키지 README를 함께 갱신합니다.
- 설정 기본값이 바뀌면 `app/core/config/README.md`를 코드와 맞춥니다.
- 기업/관리자 운영 방식이 바뀌면 `admin-company-account-classification.md`를 갱신합니다.
- 작업 과정과 검증 결과는 `docs/tasks/YYYY/MM/`와 `TASK_INDEX.md`에 기록합니다.
