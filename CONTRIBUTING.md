# 기여 가이드

> PR을 올리기 전에 이 문서를 끝까지 읽어주세요.

---

## 시작 전 필독 문서

작업 범위에 따라 아래 문서를 먼저 읽어야 합니다.

| 작업 범위 | 읽어야 할 문서 |
|---|---|
| 전체 구조 파악 | [루트 README.md](./README.md) |
| 백엔드 코드 수정 | [app/README.md](./app/README.md) |
| 테스트 추가/수정 | [tests/README.md](./tests/README.md) |
| 스크립트 실행 | [scripts/README.md](./scripts/README.md) |
| 문서 업데이트 | [docs/README.md](./docs/README.md) |
| 아키텍처 파악 | [docs/architecture.md](./docs/architecture.md) |

---

## 개발 환경 설정

```bash
git clone https://github.com/dltkdwns0730/PAZULE_AGENT.git
cd PAZULE_AGENT

# 의존성 설치 (uv 사용)
uv sync --dev

# pre-commit 훅 설치 (커밋 시 자동 포맷)
uv run pre-commit install
```

---

## 브랜치 전략

```
main          ← 직접 push 금지. PR로만 머지.
feat/<설명>   ← 새 기능
fix/<설명>    ← 버그 수정
refactor/<설명> ← 리팩터
docs/<설명>   ← 문서만 변경
```

---

## 워크플로우

### 새 기능 추가 시

```
1. feat/<issue-number>-<설명> 브랜치 생성
2. tests/ 에 실패하는 테스트 먼저 작성 (TDD)
3. 최소한의 구현 코드 작성 → 테스트 통과
4. pytest tests/ -v 로 전체 테스트 확인
5. PR 생성
```

### 버그 수정 시

```
1. fix/<설명> 브랜치 생성
2. 버그를 재현하는 테스트 작성
3. 수정 → 테스트 통과 확인
4. docs/bugfix-log.md 에 항목 추가
5. PR 생성
```

---

## PR 체크리스트

PR을 올리기 전 아래 항목을 모두 확인하세요.

### 코드 품질
- [ ] `pytest tests/ -v` 전체 통과
- [ ] 새 기능에 대한 테스트 추가 (커버리지 기준 충족)
- [ ] 함수 50줄 이하, 파일 800줄 이하
- [ ] `print()` 미사용 — `logging` 사용
- [ ] 새 상수는 `app/core/config/constants.py`에 정의
- [ ] 타입 힌트 추가

### 문서
- [ ] API 변경 시 `README.md` API 표 업데이트
- [ ] 아키텍처 변경 시 `docs/architecture.md` 업데이트
- [ ] 버그 수정 시 `docs/bugfix-log.md` 항목 추가

### 커밋
- [ ] Conventional Commits 형식 준수
  ```
  feat(council): 새 노드 추가
  fix(metadata): GPS 파싱 오류 수정
  refactor(api): 라우트 핸들러 함수 분리
  test(services): 쿠폰 발급 엣지케이스 테스트 추가
  docs(readme): 폴더 구조 설명 추가
  ```
- [ ] Co-Authored-By 등 불필요한 메타데이터 제거

---

## 커밋 메시지 형식

```
<type>(<scope>): <한국어 설명>

<변경 이유 — 원인>
<해결 방법 — 선택 이유>
<성과 — 기대 효과>
```

**type**: `feat` | `fix` | `refactor` | `test` | `docs` | `chore` | `perf`
**scope**: 변경된 모듈 (`api`, `council`, `metadata`, `models`, `services`, `core`)

---

## 코딩 규칙 요약

전체 규칙은 각 폴더의 README에 있습니다. 핵심만 요약:

```python
# ✅ 올바른 예
import logging
from app.core.config import constants

logger = logging.getLogger(__name__)

def validate_image(image_path: str) -> bool:
    """이미지 경로 유효성을 검증한다."""
    ...

# ❌ 금지 패턴
print("디버그 출력")        # logging 사용
k = 8                      # constants.COUPON_CODE_LENGTH 사용
def process(x):            # 타입 힌트 없음
    ...
```
