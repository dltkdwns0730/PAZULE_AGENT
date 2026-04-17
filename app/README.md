# app/ — 핵심 애플리케이션 패키지

> **개발자 필독**: 이 디렉터리가 PAZULE 백엔드의 전부입니다.
> 새 기능을 추가하거나 버그를 수정하기 전에 아래 구조를 먼저 파악하세요.

---

## 요청 흐름

```
HTTP 요청
  → api/routes.py                    (진입점 — 요청 정규화, 업로드 파일 처리)
    → services/answer_service.py     (오늘의 정답·힌트 조회)
    → services/mission_session_service.py (세션 생성, 제출 이력, 해시 중복 체크)
    → council/graph.py               (LangGraph 파이프라인 실행)
      → council/nodes.py             (validator / evaluator / judge / responder)
        → metadata/validator.py      (EXIF, GPS, 날짜 검증)
        → models/                    (SigLIP2, BLIP, Qwen, LLM 어댑터)
      → council/judges.py / deliberation.py  (위원회 판정)
    → services/coupon_service.py     (쿠폰 발급·사용)
  → HTTP 응답
```

---

## 서브패키지 역할

### `api/`
Flask 라우트 정의. **HTTP 레이어만** 담당한다.

| 파일 | 역할 |
|---|---|
| `routes.py` | 엔드포인트 4개 정의, 입력 검증, 서비스 레이어 호출 |

> 비즈니스 로직을 여기에 추가하지 않는다. 로직은 `services/`로 분리한다.

---

### `core/`
전역 설정 및 상수. **모든 모듈이 이곳을 참조한다.**

| 파일 | 역할 |
|---|---|
| `config/settings.py` | 환경변수 기반 런타임 설정 (`.env` 로드) |
| `config/constants.py` | 코드에 하드코딩하지 않아야 할 정적 상수 |
| `config/__init__.py` | `from app.core.config import settings, constants` re-export |
| `utils.py` | 공통 유틸리티 함수 (미션 타입 정규화, 레거시 변환 등) |
| `keyword.py` | 키워드 추출 유틸리티 |

**새 상수를 추가할 때**: 코드에 직접 숫자/문자열 리터럴을 쓰지 말고 `constants.py`에 정의한 뒤 참조한다.

---

### `council/`
**이 프로젝트의 핵심.** LangGraph 기반 멀티 비전 모델 앙상블 파이프라인.

| 파일 | 역할 |
|---|---|
| `graph.py` | LangGraph `StateGraph` 정의 — 노드 연결, 조건 분기 선언 |
| `nodes.py` | 각 그래프 노드 구현 (validator, router, evaluator, aggregator, ...) |
| `state.py` | 파이프라인 공유 상태 스키마 (`PipelineState`) |
| `judges.py` | 모델별 투표 판정 로직 |
| `deliberation.py` | 앙상블 투표 집계 및 최종 판정 |
| `aggregator.py` | 결과 집계 |

> 노드를 추가할 때 `graph.py`(연결 선언)와 `nodes.py`(구현) 두 파일을 모두 수정한다.

---

### `metadata/`
이미지 EXIF 메타데이터 검증. 어뷰징 방어 1차 레이어.

| 파일 | 역할 |
|---|---|
| `metadata.py` | EXIF GPS·날짜 추출 |
| `validator.py` | 오늘 날짜·파주 BBox 조건 검증 → `bool` 반환 |

---

### `models/`
AI 모델 어댑터 레이어. **모델 교체 시 이 디렉터리만 수정한다.**

| 파일 | 역할 |
|---|---|
| `base.py` | 모델 추상 베이스 클래스 |
| `model_registry.py` | 모델 등록/팩토리 |
| `adapter_utils.py` | 공통 어댑터 유틸리티 |
| `blip.py` | BLIP-VQA 어댑터 |
| `siglip2.py` | SigLIP2 어댑터 |
| `qwen_vl.py` | Qwen-VL API 어댑터 |
| `llm.py` | LLM(OpenAI/Gemini) 어댑터 |

---

### `legacy/plugins/`
레거시 호환용 미션 플러그인 시스템. 현재 운영 API 경로는 이 레이어를 직접 호출하지 않는다.

| 파일 | 역할 |
|---|---|
| `base.py` | 플러그인 추상 베이스 |
| `registry.py` | 플러그인 등록/디스패치 |
| `location_mission.py` | 위치 기반 미션 |
| `photo_mission.py` | 분위기 미션 |

> `main.py`에서 초기화는 하지만, 현행 운영 경로는 `api/routes.py`에서 `pipeline_app`을 직접 호출한다. 이 레이어는 CLI/호환 검증을 위한 레거시 코드다.

---

### `prompts/`
LLM 프롬프트 템플릿 관리.

| 파일/폴더 | 역할 |
|---|---|
| `registry.py` | 프롬프트 레지스트리 (싱글턴) |
| `loader.py` | YAML 템플릿 파일 로더 |
| `templates/*.yaml` | 프롬프트 원문 (코드와 분리 관리) |

---

### `services/`
비즈니스 로직 서비스 레이어.

| 파일 | 역할 |
|---|---|
| `legacy/mission_service.py` | 레거시 미션 실행 서비스 (CLI/플러그인 호환용) |
| `mission_session_service.py` | 세션 관리, 이미지 해시 중복 체크 |
| `coupon_service.py` | 쿠폰 발급·조회·사용 (JSON 파일 스토리지) |
| `answer_service.py` | 오늘의 정답 키워드 조회 |

> 현재 운영 API 경로는 `app/legacy/mission_service.py`를 거치지 않는다. 실제 제출 처리는 `app/api/routes.py`에서 `pipeline_app.invoke(...)`를 직접 호출한다.

---

## 코딩 규칙

- 함수 50줄 이하, 파일 800줄 이하
- `print()` 사용 금지 → `logger = logging.getLogger(__name__)` 사용
- 새 상수는 반드시 `core/config/constants.py`에 정의
- 타입 힌트 필수: 모든 함수 파라미터와 반환값
- 테스트 없이 PR 올리지 않는다 → [`tests/`](../tests/README.md) 참고
