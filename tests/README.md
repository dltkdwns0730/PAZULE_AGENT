# tests/ — pytest 자동화 테스트

> **PR 올리기 전 필독**: 모든 테스트가 통과해야 머지할 수 있습니다.
> 새 기능을 추가했다면 대응하는 테스트도 함께 추가하세요.

---

## tests/ vs scripts/ — 무엇이 다른가?

| 구분 | `tests/` | `scripts/` |
|---|---|---|
| 실행 주체 | pytest (자동) | 개발자 (수동) |
| 판정 방식 | `assert` 문 (코드) | `print` 출력 (눈) |
| 외부 의존성 | mock으로 차단 | 실제 모델·API 사용 |
| 실행 시점 | 커밋·PR마다 자동 | 필요할 때만 수동 |
| CI 포함 | ✅ | ❌ |
| 목적 | 회귀 방지, 동작 보증 | 탐색, 디버깅, 성능 측정 |

---

## 실행 방법

```bash
# 전체 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ -v --cov=app --cov-report=term-missing

# 특정 모듈만
pytest tests/council/ -v
pytest tests/core/ -v

# 특정 파일만
pytest tests/council/test_nodes_helpers.py -v

# 특정 테스트 클래스/함수만
pytest tests/council/test_nodes_helpers.py::TestBuildBypassVotes -v
```

---

## 디렉터리 구조

```
tests/
├── core/                            # app/core/ 모듈 테스트
│   ├── test_constants.py            # constants.py 상수 타입·값 검증 (33개)
│   ├── test_config_import.py        # config 패키지 import 하위 호환성 (18개)
│   └── test_coupon_constants_usage.py  # CouponService 상수 참조 검증 (11개)
│
├── council/                         # app/council/ 모듈 테스트
│   ├── test_nodes.py                # 그래프 노드 단위 테스트
│   ├── test_nodes_helpers.py        # 분리된 헬퍼 함수 단위 테스트 (35개)
│   └── test_pipeline_integration.py # 파이프라인 통합 테스트
│
├── metadata/                        # app/metadata/ 모듈 테스트
│   └── test_validator_refactor.py   # validator 타입 안전성 테스트 (10개)
│
├── test_coupon_service.py           # CouponService 비즈니스 로직 테스트
├── test_docs_audit.py               # docs_audit 도구 테스트
└── test_nodes_logic.py              # 노드 로직 테스트
```

---

## 커버리지 기준

| 코드 유형 | 최소 커버리지 |
|---|---|
| 일반 코드 | 80% 이상 |
| `council/` (핵심 파이프라인) | 100% |
| `services/coupon_service.py` (금융) | 100% |
| `metadata/validator.py` (보안) | 100% |

---

## 테스트 작성 원칙

### 파일 위치 규칙
- `app/council/nodes.py` 테스트 → `tests/council/test_nodes.py`
- `app/services/coupon_service.py` 테스트 → `tests/test_coupon_service.py`
- 앱 구조를 그대로 `tests/` 아래에 미러링한다.

### 필수 케이스
- [ ] 정상 입력 (happy path)
- [ ] `None` / 빈 문자열 입력
- [ ] 예외 발생 시 동작
- [ ] 경계값 (최소, 최대)

### Mock 사용 원칙
- 외부 API, AI 모델, 파일 I/O는 반드시 mock으로 대체
- `patch("app.council.nodes.settings")` 처럼 **사용 위치**를 패치한다

### 명명 규칙
```python
class TestCheckImagePresence:          # 테스트 대상 함수명 → PascalCase
    def test_valid_path_returns_true(self):  # 입력 조건 + 기대 결과
```

---

## 자주 묻는 질문

**Q. 모델 추론이 필요한 기능은 어떻게 테스트하나요?**
A. `unittest.mock.patch`로 모델 함수를 mock하고 반환값을 직접 지정합니다. 실제 모델 추론 테스트는 `scripts/`의 수동 스크립트를 사용하세요.

**Q. 테스트가 환경변수에 영향을 받아요.**
A. `patch("app.council.nodes.settings")` 처럼 settings 객체를 mock해서 테스트를 환경변수로부터 격리합니다.

**Q. 기존 테스트 2개가 FAILED로 뜨는데요?**
A. `test_evaluator_atmosphere`, `test_full_pipeline_gate_blocked`는 `.env`의 `BYPASS_MODEL_VALIDATION` / `SKIP_METADATA_VALIDATION` 설정이 mock을 무력화하는 구조적 문제로, 별도 이슈로 추적 중입니다.
