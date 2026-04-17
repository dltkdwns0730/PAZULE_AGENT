# docs/ — 프로젝트 문서

> 코드 변경이 아키텍처나 API에 영향을 준다면 관련 문서도 함께 업데이트하세요.

---

## 문서 목록

| 파일 | 대상 독자 | 내용 |
|---|---|---|
| [`architecture.md`](./architecture.md) | 개발자 | 시스템 아키텍처, LangGraph 파이프라인 설계, 상태 흐름, Council 3-Tier 에스컬레이션 |
| [`refactor-audit.md`](./refactor-audit.md) | 개발자 / 리뷰어 | 현재 운영 구조, 데이터 파이프라인, 레거시 후보와 삭제 전 검증 포인트 |
| [`ci-cd-architecture.md`](./ci-cd-architecture.md) | DevOps / 개발자 | GitHub Actions CI/CD 파이프라인 설계, Docker 멀티스테이지 빌드, ghcr.io 배포 |
| [`changelog.md`](./changelog.md) | 전체 | 버전별 변경 이력 |
| [`bugfix-log.md`](./bugfix-log.md) | 개발자 | 버그 수정 명세서 (발견 경위, 원인, 해결 방법) |
| [`commercialization-plan.md`](./commercialization-plan.md) | 기획 / 리더 | 상용화 로드맵, 프로덕션 마일스톤 |
| [`doc-guide.md`](./doc-guide.md) | 문서 작성자 | 내부 문서 작성 규칙 및 템플릿 |

---

## 서브디렉터리

### `benchmarks/`
AI 모델 성능 측정 보고서.

| 파일 | 내용 |
|---|---|
| `baseline-report.md` | 초기 기준 성능 측정 결과 |
| `benchmark-template.md` | 벤치마크 보고서 작성 템플릿 |

> 새 벤치마크 결과는 `benchmark-template.md`를 복사해 작성한다.
> 스크립트 실행: [`scripts/benchmark_siglip.py`](../scripts/README.md)

### `assets/`
README 및 문서에 삽입하는 이미지 파일.

---

## 문서 업데이트 원칙

- **아키텍처 변경** → `architecture.md` 업데이트 필수
- **API 추가/변경** → 루트 `README.md`의 API 표 업데이트
- **버그 수정** → `bugfix-log.md`에 항목 추가
- **버전 릴리스** → `changelog.md`에 항목 추가
- **벤치마크 측정** → `benchmarks/` 하위에 날짜 기반 파일로 저장
