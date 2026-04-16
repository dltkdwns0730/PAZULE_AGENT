# scripts/ — 개발자용 수동 실행 스크립트

> **주의**: 이 폴더의 스크립트는 CI에 포함되지 않습니다.
> 자동화 테스트가 필요하면 [`tests/`](../tests/README.md)를 사용하세요.

---

## scripts/ vs tests/ — 무엇이 다른가?

| 구분 | `scripts/` | `tests/` |
|---|---|---|
| 실행 주체 | 개발자 (수동) | pytest (자동) |
| 판정 방식 | 눈으로 확인 | `assert` (코드) |
| 외부 의존성 | 실제 모델·API 사용 | mock으로 차단 |
| 실행 시점 | 필요할 때만 | 커밋·PR마다 자동 |
| CI 포함 | ❌ | ✅ |
| 목적 | 탐색, 디버깅, 성능 측정 | 회귀 방지, 동작 보증 |

---

## 스크립트 목록

### `simulate_cli.py` — CLI 게임 시뮬레이션
웹 서버 없이 터미널에서 미션 플로우를 직접 체험한다.

```bash
uv run scripts/simulate_cli.py
```

**언제 쓰나**: 새 미션 플로우를 개발했을 때 E2E 동작을 빠르게 눈으로 확인할 때.

---

### `test_pipeline_mock.py` — 파이프라인 Mock 실행
실제 AI 모델 없이 파이프라인 전체 흐름을 확인한다. 모델 미설치 환경에서도 동작.

```bash
uv run scripts/test_pipeline_mock.py
```

**언제 쓰나**: 모델 없이 LangGraph 노드 흐름, 상태 전달, 분기 로직을 확인할 때.

> 모델 동작이 아닌 **흐름**을 확인하는 용도. 모델 동작 검증은 `verify_components.py` 사용.

---

### `verify_components.py` — 컴포넌트 개별 검증
4가지 핵심 컴포넌트를 독립적으로 호출해 PASS/FAIL을 리포트한다.

```bash
# 기본 실행 (샘플 이미지 사용)
uv run scripts/verify_components.py

# 특정 이미지로 실행
uv run scripts/verify_components.py --image "C:\path\to\photo.jpg"

# 정답·미션 타입 지정
uv run scripts/verify_components.py --answer "한길책박물관" --mission-type location
```

**검증 항목**:
1. GPS 메타데이터 검증
2. VLM 모델 프로브 (Qwen / BLIP / SigLIP2)
3. 앙상블 취합 + 판정
4. LLM 힌트 생성 (오답 시나리오)

**언제 쓰나**: 모델 교체 후 각 컴포넌트가 정상 동작하는지 수동 검증할 때.

---

### `benchmark_siglip.py` — SigLIP2 성능 벤치마크
SigLIP2 모델의 정확도·속도를 측정하고 벤치마크 리포트를 생성한다.

```bash
uv run scripts/benchmark_siglip.py
```

**언제 쓰나**: 모델 버전 업그레이드 전후 성능 비교, 가중치 튜닝 효과 측정.
결과는 `docs/benchmarks/`에 저장한다.

---

## 공통 주의사항

- 실제 AI 모델을 로드하므로 **GPU 메모리와 API 크레딧을 소모**한다.
- `.env`의 API 키가 설정되어 있어야 Qwen VL API를 호출할 수 있다.
- 스크립트 실행 결과는 리포에 커밋하지 않는다 (탐색·디버깅 용도).
