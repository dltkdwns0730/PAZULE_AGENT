# PAZULE 리팩터 감사 문서

> 최종 갱신: 2026-04-17
> 목적: 현재 서비스 아키텍처, 런타임 데이터 파이프라인, 삭제 전 검증이 필요한 레거시 후보를 한 문서에서 확인한다.

---

## 범위

- 대상 루트: `PAZULE/`
- 중점 확인 항목:
  - 현재 운영 경로에 가까운 런타임 구조
  - 런타임 데이터 흐름과 영속 저장 파일
  - 삭제 전에 검증이 필요한 레거시 코드/프로토타입 파일
- 이번 삭제 검토에서 제외:
  - `data/assets/`
  - `docs/assets/`
  - 캐시 및 빌드 산출물

---

## 구조 요약

- 백엔드 런타임:
  - `main.py`가 `Flask`, CORS, 프롬프트/모델/플러그인 레지스트리를 초기화하고 `app.api.routes`를 등록한다.
  - `app/api/routes.py`가 HTTP 요청 처리, 업로드 검증, 임시 파일 수명주기, JSON 응답을 담당한다.
  - `app/council/graph.py`가 미션 제출 시 사용하는 LangGraph 파이프라인을 컴파일한다.
- 프런트엔드 런타임:
  - `front/src/App.jsx`가 현재 활성 React Router 진입점이다.
  - `front/src/services/api.js`와 `front/src/hooks/useMission.js`가 현재 프런트 API 연동 계층이다.
- 영속 저장:
  - `data/answer.json`은 미션 후보 풀을 저장한다.
  - `data/current_answer.json`은 당일 선택된 미션 쌍을 캐시한다.
  - `data/mission_sessions.json`은 미션 세션과 제출 이력을 저장한다.
  - `data/coupons.json`은 발급/사용된 쿠폰을 저장한다.

---

## 현재 런타임 데이터 파이프라인

1. 힌트 조회 / 미션 시작
   - `answer_service.py`가 `answer.json`을 읽는다.
   - `get_today_answers()`가 `current_answer.json`을 읽거나 새로 갱신한다.
   - `/api/mission/start`가 `mission_sessions.json`에 세션을 생성한다.

2. 미션 제출
   - `routes.py`가 업로드를 검증하고 제출 이미지를 임시 파일로 저장한다.
   - `pipeline_app.invoke(initial_state)`가 아래 LangGraph 경로를 실행한다.
     - `validator`
     - `router`
     - `evaluator`
     - `aggregator`
     - `council`
     - `judge`
     - `policy`
     - `responder`
   - 라우트의 `finally` 블록에서 요청용 임시 파일을 삭제한다.
   - `mission_session_service.record_submission()`이 이미지 해시와 최신 판정 결과를 `mission_sessions.json`에 기록한다.

3. 쿠폰 흐름
   - `/api/coupon/issue`가 최신 미션 판정을 읽고 `coupons.json`에 발급 정보를 기록한다.
   - `/api/coupon/redeem`가 `coupons.json`의 쿠폰 상태를 갱신한다.

---

## 정합성 평가

- 현재 기준으로 일치하는 점:
  - 런타임 백엔드는 `Flask + LangGraph` 구조다.
  - 런타임 프런트는 `api.js`와 `useMission.js`를 사용한다.
  - 세션/쿠폰 저장 경로가 `data/` 아래로 집중되어 있다.
- 리팩터 전 불일치했던 점:
  - 최상위 문서가 여전히 `FastAPI + Uvicorn`을 안내했다.
  - `main.py`가 존재하지 않는 `scripts/test_real_models.py`를 가리켰다.
  - `app/README.md`가 구 레거시 서비스 파일을 현행 흐름처럼 설명했지만 실제 제출은 `pipeline_app`으로 직행했다.
  - 활성 UI가 프로필 플레이스홀더에서 `/legacy`로 바로 이동하도록 노출하고 있었다.

---

## 레거시 후보

| 경로 | 현재 역할 | 레거시로 보는 이유 | 삭제 전 확인 포인트 |
|---|---|---|---|
| `app/legacy/mission_service.py` | 과거 미션 실행기 | 메인 API는 호출하지 않고, 호환 경로만 참조한다. | CLI/플러그인을 폐기하거나 `pipeline_app` 기반으로 재작성한 뒤 제거 |
| `app/legacy/plugins/base.py` | 플러그인 추상 계층 | 운영 경로는 플러그인 디스패치를 사용하지 않는다. | 외부 통합이나 수동 도구가 플러그인 API를 import하지 않는지 확인 |
| `app/legacy/plugins/registry.py` | 플러그인 레지스트리 | 부팅 시 초기화되지만 `routes.py`, `graph.py`에서 직접 사용되지 않는다. | 부팅 시 플러그인 등록을 제거해도 회귀가 없는지 확인 |
| `app/legacy/plugins/location_mission.py` | `run_mission1()` 래퍼 | 레거시 미션 서비스 래퍼다. | `app/legacy/mission_service.py`와 같은 기준으로 검증 |
| `app/legacy/plugins/photo_mission.py` | `run_mission2()` 래퍼 | 레거시 미션 서비스 래퍼다. | `app/legacy/mission_service.py`와 같은 기준으로 검증 |
| `scripts/legacy/legacy_cli_simulation.py` | CLI 스모크 경로 | 현재 LangGraph 제출 경로가 아니라 레거시 미션 서비스를 실행한다. | CLI 호환 점검이 정말 필요한 경우에만 유지 |

---

## 권장 다음 단계

1. 현재 운영 경로를 `Flask API -> LangGraph pipeline -> JSON persistence`로 고정한다.
2. 레거시 파일은 즉시 삭제하지 말고 승인 기반 정리 배치로 다룬다.
3. CLI 검증이 필요하다면 `scripts/legacy/legacy_cli_simulation.py`를 `initial_state` 구성 후 `pipeline_app` 직접 호출 방식으로 재작성한다.
4. 그 재작성 이후 플러그인 계층과 `app/legacy/mission_service.py`를 같은 변경 세트에서 제거한다.
5. 남은 정리 후보는 `app/legacy/`와 `scripts/legacy/` 경로의 실제 보존 필요성으로 좁힌다.

---

## 이번 정리에서 제거한 항목

- `front/src/designs/` 정적 프로토타입 HTML 묶음
- `front/download.ps1` 디자인 다운로드 스크립트
- `front/src/legacy/LegacyMissionApp.jsx` 및 `/legacy` 라우트
- `app/models/clip.py`

위 항목들은 코드/문서 참조가 없고 React 런타임에도 연결되지 않아 제거했다.
