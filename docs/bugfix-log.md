# PAZULE Bugfix Log

> **분류**: 레퍼런스 · **버전**: v2.4.1 · **최종 수정**: 2026-04-14
>
> TDD 기반으로 수정된 버그별 원인·수정·검증 이력.

---

## 도입 배경

이 문서는 **2026-04-14부터 도입된 TDD(Test-Driven Development) 기반 버그 추적 체계**입니다.

- 이전(v1.0 ~ v2.4.0)까지의 변경 이력은 [`docs/changelog.md`](./changelog.md)에서 확인
- 이 문서는 v2.4.1 이후 TDD 사이클로 수정된 버그를 상세 추적하는 전용 레퍼런스
- 각 항목은 **원인 → 재현 시나리오 → 수정 내용 → 검증** 순서로 기록

---

## 프로젝트 버전 대응표

> 다른 컨텍스트/LLM에서 이 프로젝트를 파악할 때 참조하는 버전 기준표.
> 버그 ID(`BUG-NNN`)는 이 문서에서만 사용하며, changelog의 버전(`v2.x`)과 독립적으로 관리됩니다.

| 프로젝트 버전 | 기간 | 주요 내용 | 참조 문서 | 버그 ID 범위 |
|--------------|------|-----------|-----------|-------------|
| v1.0 | 팀 프로젝트 | 수상작 (파주시장상), BLIP+CLIP+GPT-4o-mini | `changelog.md#v1.0` | 없음 (체계 미도입) |
| v2.0.0 ~ v2.0.x | 개인 고도화 시작 | LangGraph Council 아키텍처, 서비스 재설계 | `changelog.md#v2.0` | 없음 |
| v2.1.0 ~ v2.1.x | API + CLI + Frontend | Flask API, React 19 SPA, CLI 게임 루프 | `changelog.md#v2.1` | 없음 |
| v2.2.0 ~ v2.2.x | 멀티모델 앙상블 | SigLIP2, Qwen VL, ModelRegistry | `changelog.md#v2.2` | 없음 |
| v2.3.0 ~ v2.3.x | 파이프라인 통합 | 3-Tier 에스컬레이션, UI 개선, 쿠폰 멱등성 | `changelog.md#v2.3` | 없음 |
| v2.4.0 | 문서화 | architecture.md, commercialization-plan.md | `changelog.md#v2.4` | 없음 |
| **v2.4.1** | **2026-04-14** | **TDD 도입 + 프론트엔드 버그 4건 수정** | **이 문서** | **ENV-001, BUG-001 ~ BUG-004** |

**핵심 구분 원칙:**
- `v2.4.0` 이전 — changelog에만 기록, 버그 ID 없음
- `v2.4.1` 이후 — changelog(요약) + bugfix-log(상세 + ID) 병행 관리

---

## 항목 템플릿

> 새 버그 추가 시 아래 템플릿을 복사해 사용

```markdown
## <ID> — <한 줄 제목>

| 항목 | 내용 |
|------|------|
| **분류** | BUG / ENV / PERF / SEC |
| **심각도** | CRITICAL / HIGH / MEDIUM / LOW |
| **발견 경로** | 코드 리뷰 / 테스트 / 사용자 리포트 |
| **수정 커밋** | `<hash>` |
| **수정 파일** | `path/to/file.js` |
| **테스트 파일** | `path/to/file.test.js` |

### 원인 (Root Cause)
...

### 재현 시나리오
...

### 수정 내용
...

### 검증
...

### 영향 범위
...
```

**ID 부여 규칙:**
- `BUG-NNN` — 기능 버그 (3자리 제로패딩)
- `ENV-NNN` — 환경/인프라 작업
- `PERF-NNN` — 성능 문제
- `SEC-NNN` — 보안 취약점

---

## v2.4.1 — TDD 기반 프론트엔드 버그 수정 (2026-04-14)

> 관련 브랜치: `fix/front-tdd-api-hooks-photo-bugs`
> 관련 커밋: `0ed9608` → `01f52cb` → `3165017` → `f69d982`

---

### ENV-001 — 테스트 프레임워크 부재

| 항목 | 내용 |
|------|------|
| **분류** | ENV |
| **심각도** | HIGH |
| **발견 경로** | TDD 도입 계획 수립 중 확인 |
| **수정 커밋** | `0ed9608` |
| **수정 파일** | `front/package.json`, `front/vitest.config.js`, `front/src/test/setup.js` |
| **테스트 파일** | 해당 없음 (환경 구성) |

#### 원인 (Root Cause)
`front/` 디렉터리에 테스트 프레임워크가 전혀 설정되어 있지 않았음.
`package.json`에 `test` 스크립트 없음, Vitest/Jest 의존성 없음.

#### 재현 시나리오
```bash
cd front && npm test
# → "Missing script: test" 에러
```

#### 수정 내용
- `@vitest/ui`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom` 설치
- `front/vitest.config.js` 신규 생성 (jsdom 환경, globals, setupFiles 설정)
- `front/src/test/setup.js` 신규 생성 (`@testing-library/jest-dom` 매처 초기화)
- `package.json` test 스크립트 추가

```js
// front/vitest.config.js
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
  },
});
```

**Jest 대신 Vitest 선택 이유:**
- 기존 `vite.config.js` 재사용 가능 (별도 Babel 설정 불필요)
- ES Module 네이티브 지원 (React 19 + Vite 7 스택과 호환)
- `vi.useFakeTimers()`, `vi.spyOn()` 등 Jest 호환 API 제공

#### 검증
```bash
npm test  # → "No test files found" (에러 없이 실행 확인)
```

#### 영향 범위
`front/` 전체. 이후 BUG-001 ~ BUG-004 테스트 작성의 전제 조건.

---

### BUG-001 — API fetch 무한 대기 (UI 영구 잠금)

| 항목 | 내용 |
|------|------|
| **분류** | BUG |
| **심각도** | HIGH |
| **발견 경로** | 코드 리뷰 |
| **수정 커밋** | `01f52cb` |
| **수정 파일** | `front/src/services/api.js` |
| **테스트 파일** | `front/src/test/services/api.test.js` |

#### 원인 (Root Cause)
`api.js`의 모든 `fetch()` 호출에 timeout이 없었음.
네트워크 지연 또는 서버 무응답 시 Promise가 영원히 pending 상태를 유지,
호출부의 `isLoading`이 `true`로 고정되어 UI 전체가 잠기는 상태 발생.

```js
// 수정 전 — timeout 없음
const response = await fetch(`${API_BASE}/get-today-hint?mission_type=${missionType}`);
```

#### 재현 시나리오
1. 백엔드 서버를 중단한 상태에서 미션 시작
2. `isLoading === true` 상태가 무한 지속
3. UI 버튼 전부 비활성화, 사용자가 앱을 종료할 방법 없음

#### 수정 내용
`AbortController + setTimeout` 조합의 `fetchWithTimeout()` 헬퍼 추가,
4개 엔드포인트(`getTodayHint`, `startMission`, `submitMission`, `issueCoupon`) 일괄 적용.

```js
// front/src/services/api.js
const FETCH_TIMEOUT_MS = 10_000;

function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    return fetch(url, { ...options, signal: controller.signal }).finally(() => {
        clearTimeout(timeoutId);
    });
}
```

**`AbortSignal.timeout()` 대신 `AbortController` 선택 이유:**
- jsdom 테스트 환경에서 `AbortSignal.timeout()`의 호환성 불완전
- `vi.useFakeTimers()`로 `setTimeout`을 직접 제어해 결정적(deterministic) 테스트 가능

#### 검증
```js
// front/src/test/services/api.test.js
it.each([
  ['getTodayHint', () => api.getTodayHint('location')],
  ['startMission', () => api.startMission({ mission_type: 'location', user_id: 'guest' })],
  ['submitMission', () => api.submitMission(new FormData())],
  ['issueCoupon', () => api.issueCoupon('mission-xyz')],
])('%s이 10초 내 응답 없으면 reject한다', async (_name, call) => {
  vi.spyOn(global, 'fetch').mockImplementation(hangingFetch);
  const promise = call();
  promise.catch(() => {});
  await vi.advanceTimersByTimeAsync(11000);
  await expect(promise).rejects.toThrow();
});
```

#### 영향 범위
`front/src/services/api.js` 전체 (`getTodayHint`, `startMission`, `submitMission`, `issueCoupon`).

---

### BUG-002 — fetchHint isLoading 미관리 (스피너 미표시)

| 항목 | 내용 |
|------|------|
| **분류** | BUG |
| **심각도** | MEDIUM |
| **발견 경로** | 코드 리뷰 |
| **수정 커밋** | `3165017` |
| **수정 파일** | `front/src/hooks/useMission.js` |
| **테스트 파일** | `front/src/test/hooks/useMission.test.js` |

#### 원인 (Root Cause)
`useMission.js`의 `fetchHint()` 함수에만 `setIsLoading(true/false)` 호출이 누락됨.
`startMission`, `submitPhoto`, `issueCoupon`은 모두 `isLoading` 관리가 올바르게 구현됨.
힌트 로딩 중 `AILoadingOverlay`가 표시되지 않아 사용자가 앱이 멈춘 것으로 오인 가능.

```js
// 수정 전 — setIsLoading 호출 없음
const fetchHint = async (missionType) => {
    setError(null);  // setIsLoading(true) 누락
    try {
        const data = await api.getTodayHint(missionType);
        store.setHint(data.hint);
        return data.hint;
    } catch (err) { ... }
    // finally { setIsLoading(false) } 누락
};
```

#### 재현 시나리오
1. 미션 홈 화면 진입 시 힌트 로딩 시작
2. 네트워크 지연 상황에서도 AI 로딩 스피너가 표시되지 않음
3. 화면이 멈춘 것처럼 보임

#### 수정 내용
`setIsLoading(true)` 진입부 추가, `finally` 블록에 `setIsLoading(false)` 추가.
기존 3개 함수(`startMission`, `submitPhoto`, `issueCoupon`)와 동일한 패턴으로 통일.

```js
// front/src/hooks/useMission.js
const fetchHint = async (missionType) => {
    setIsLoading(true);   // 추가
    setError(null);
    try {
        const data = await api.getTodayHint(missionType);
        store.setHint(data.hint);
        return data.hint;
    } catch (err) {
        console.error('Failed to fetch hint:', err);
        store.setHint('힌트를 불러올 수 없습니다.');
        return null;
    } finally {
        setIsLoading(false);  // 추가
    }
};
```

#### 검증
```js
// front/src/test/hooks/useMission.test.js
it('fetchHint 호출 중 isLoading이 true다', async () => {
  let resolve;
  api.getTodayHint.mockReturnValue(new Promise((r) => { resolve = r; }));
  const { result } = renderHook(() => useMission());

  act(() => { result.current.fetchHint('location'); });
  expect(result.current.isLoading).toBe(true);  // 로딩 중 확인

  await act(async () => { resolve({ hint: 'Find the bookshelf' }); });
  expect(result.current.isLoading).toBe(false); // 완료 후 확인
});
```

#### 영향 범위
`front/src/hooks/useMission.js`의 `fetchHint` 함수.
`MissionHome.jsx`에서 `fetchHint` 호출 시 `AILoadingOverlay` 표시 여부.

---

### BUG-003 — PhotoSubmission stale state race condition

| 항목 | 내용 |
|------|------|
| **분류** | BUG |
| **심각도** | CRITICAL |
| **발견 경로** | 코드 리뷰 |
| **수정 커밋** | `f69d982` |
| **수정 파일** | `front/src/pages/PhotoSubmission.jsx` |
| **테스트 파일** | `front/src/test/pages/PhotoSubmission.test.jsx` |

#### 원인 (Root Cause)
`handleSubmit` 내에서 `setAttemptsLeft()` 호출 후 즉시 `attemptsLeft`를 비교하는 stale closure 문제.
React의 `useState`는 setState 호출 즉시 state를 갱신하지 않고 다음 렌더 사이클에 반영하므로,
`attemptsLeft`는 이전 렌더의 값(stale value)을 참조해 navigate 조건 판단이 빗나감.

```js
// 수정 전 — stale state 참조
const newAttemptsLeft = Math.max(0, attemptsLeft - 1);
setAttemptsLeft(newAttemptsLeft);
setRetryError(result.error || result.message || 'Verification Failed.');

if (attemptsLeft <= 0) {  // ← attemptsLeft는 아직 이전 값 (stale)
    navigate('/mission/result');
}
```

#### 재현 시나리오
1. 사진 제출 → 실패 (1차: attemptsLeft: 3 → 2)
2. 사진 제출 → 실패 (2차: attemptsLeft: 2 → 1)
3. 사진 제출 → 실패 (3차: attemptsLeft: 1 → 0)
   - 기대: `/mission/result`로 이동
   - 실제: `attemptsLeft`가 여전히 `1`을 참조해 navigate 미실행

#### 수정 내용
`setAttemptsLeft()` 전에 `newAttemptsLeft` 지역 변수로 새 값을 확정,
navigate 조건 판단을 지역 변수 기준으로 변경. 클로저 캡처 문제 원천 차단.

```js
// 수정 후 — 지역 변수로 확정 후 비교
const newAttemptsLeft = Math.max(0, attemptsLeft - 1);
setAttemptsLeft(newAttemptsLeft);
setRetryError(result.error || result.message || 'Verification Failed. Target not found.');

if (newAttemptsLeft <= 0) {  // ← 확정된 지역 변수 사용
    navigate('/mission/result');
}
```

추가로 매직 넘버 `3`을 `MAX_ATTEMPTS` 상수로 추출.

```js
const MAX_ATTEMPTS = 3;
// ...
const [attemptsLeft, setAttemptsLeft] = useState(MAX_ATTEMPTS);
```

#### 검증
```js
// front/src/test/pages/PhotoSubmission.test.jsx
it('3번째 실패 후 /mission/result로 이동한다', async () => {
  // 1차, 2차 실패 — navigate 없어야 함
  fireEvent.click(btn);
  await waitFor(() => expect(submitPhoto).toHaveBeenCalledTimes(1));
  expect(mockNavigate).not.toHaveBeenCalledWith('/mission/result');

  fireEvent.click(btn);
  await waitFor(() => expect(submitPhoto).toHaveBeenCalledTimes(2));
  expect(mockNavigate).not.toHaveBeenCalledWith('/mission/result');

  // 3차 실패 — navigate 필수
  fireEvent.click(btn);
  await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/mission/result'));
});
```

#### 영향 범위
`front/src/pages/PhotoSubmission.jsx`의 `handleSubmit` 함수.
미션 실패 3회 후 결과 페이지 이동 흐름 전체.

---

### BUG-004 — PhotoSubmission route guard 부재 (미인증 직접 접근)

| 항목 | 내용 |
|------|------|
| **분류** | BUG |
| **심각도** | MEDIUM |
| **발견 경로** | 코드 리뷰 |
| **수정 커밋** | `f69d982` |
| **수정 파일** | `front/src/pages/PhotoSubmission.jsx` |
| **테스트 파일** | `front/src/test/pages/PhotoSubmission.test.jsx` |

#### 원인 (Root Cause)
`/mission/submit` 경로에 route guard가 없었음.
활성 미션(`missionId`)이 없는 상태에서 URL을 직접 입력하거나
브라우저 뒤로가기로 접근 시 `missionId === null`인 채로 페이지가 렌더링됨.
이후 제출 시도 시 `'Mission not started'` 에러 발생 또는 빈 화면 노출.

#### 재현 시나리오
1. 브라우저에서 `/mission/submit` 직접 입력
2. `missionId`가 null → 페이지는 정상 렌더링되나 submit 시 에러
3. 또는 미션 완료 후 브라우저 뒤로가기로 재진입 시 동일 현상

#### 수정 내용
`useEffect`로 `missionId` 부재 시 즉시 `'/'`로 redirect.

```js
// front/src/pages/PhotoSubmission.jsx
useEffect(() => {
    if (!store.missionId) {
        navigate('/');
    }
}, [store.missionId]);
```

#### 검증
```js
// front/src/test/pages/PhotoSubmission.test.jsx
it('missionId가 null이면 "/"로 redirect한다', async () => {
  useMissionStore.mockReturnValue({ missionId: null, ... });
  render(<MemoryRouter><PhotoSubmission /></MemoryRouter>);
  await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'));
});
```

#### 영향 범위
`front/src/pages/PhotoSubmission.jsx` 마운트 시점.
URL 직접 접근, 브라우저 뒤로가기, 세션 만료 후 재진입 시나리오 전체.

---

## 테스트 실행 결과

```
Test Files  3 passed (3)
Tests       9 passed (9)

front/src/test/services/api.test.js      — 4 tests (BUG-001)
front/src/test/hooks/useMission.test.js  — 2 tests (BUG-002)
front/src/test/pages/PhotoSubmission.test.jsx — 3 tests (BUG-003, BUG-004)
```

```bash
# 재실행 명령
cd front && npm test
```
