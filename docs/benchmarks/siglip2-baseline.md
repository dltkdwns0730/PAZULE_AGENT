# SigLIP2 Benchmark — v1 Baseline

> **분류**: 벤치마크 · **버전**: v1 · **최종 수정**: 2026-04-07
>
> 모델: `google/siglip2-base-patch16-224` · 장비: CPU (torch 2.10.0, transformers 5.2.0)
> 이미지: `front/src/assets/intro5.jpg` (활판공방 인쇄기)

## 목적

SigLIP2 단독 성능의 기준선(baseline) 확보.
현재 파이프라인의 프롬프트 구조(`"a photo of {한국어 키워드}"`)가 모델 성능에 미치는 영향 파악.

---

## Test 1: Location 미션 (한국어 프롬프트)

프롬프트 형식: `"a photo of {landmark}"`

| 랜드마크 | Score | 판정 (threshold 0.70) |
|---|---|---|
| **활판공방 인쇄기 (정답)** | **0.2838** | **FAIL** |
| 활돌이 | 0.0013 | FAIL |
| 네모탑 | 0.0009 | FAIL |
| 나남출판사 | 0.0003 | FAIL |
| 마법천자문 손오공 | 0.0003 | FAIL |
| 지혜의숲 조각상 | 0.0001 | FAIL |
| 피노지움 조각상 | 0.0001 | FAIL |
| 로드킬 부엉이 | 0.0000 | FAIL |
| 지혜의숲 고양이 | 0.0000 | FAIL |
| 창틀 피노키오 | 0.0000 | FAIL |

**결과:**
- 정답 score 0.28 → 임계값 0.70 미달 (FALSE NEGATIVE)
- 정답/오답 gap은 0.28로 상대적 순위는 정확
- False Positive: 0개

---

## Test 2: 프롬프트 언어 비교 (동일 이미지)

| 프롬프트 | Score |
|---|---|
| `a photo of 활판공방 인쇄기` (KR) | 0.2838 |
| `a photo of a printing press sculpture` (EN literal) | 0.9194 |
| `a photo of an old rusty printing press with Korean metal letters` (EN descriptive) | 0.7721 |
| `an outdoor sculpture of a vintage printing machine covered in metal characters` (EN scene) | 0.9958 |
| `printing press sculpture` (EN short) | 0.6546 |
| `a metal sculpture outdoors` (EN generic) | 0.0041 |

**결과:**
- 한국어 → 0.28, 영어 → 0.65 ~ 0.99
- 동일 모델, 동일 이미지에서 **프롬프트 언어에 의해 score가 3~4배 차이**
- 모델 성능 자체는 문제 없음. 프롬프트 언어가 병목

---

## Test 3: 오답 랜드마크 영어 프롬프트

영어 프롬프트 사용 시 False Positive 발생 여부 확인.

| 오답 설명 | Score |
|---|---|
| monkey boy statue | 0.0000 |
| owl sculpture made of tires | 0.0000 |
| building covered in ivy | 0.0001 |
| pink cartoon character statue | 0.0000 |
| cat sculpture in a display case | 0.0000 |
| square tower sculpture | 0.0000 |
| sitting figure with binoculars | 0.0000 |
| pinocchio on a window frame | 0.0000 |
| pinocchio scene sculpture | 0.0000 |

**결과:**
- 영어 프롬프트 시 오답 score 전부 0.0001 이하
- False Positive: 0개
- 정답(0.77) vs 최고 오답(0.0001) gap: **0.77**

---

## Test 4: 분위기 키워드 한국어 vs 영어

| 키워드 | KR Score | EN Score |
|---|---|---|
| 차분한 / calm | 0.0000 | 0.0000 |
| 화사한 / bright and colorful | 0.0000 | 0.0000 |
| 활기찬 / lively and energetic | 0.0000 | 0.0000 |
| 옛스러운 / old-fashioned and vintage | 0.0004 | 0.0009 |
| 자연적인 / natural | 0.0000 | 0.0000 |
| 신비로운 / mysterious | 0.0000 | 0.0000 |
| 웅장한 / grand and majestic | 0.0000 | 0.0000 |

**결과:**
- 활판 인쇄기 사진에 분위기 매칭 자체가 부적합 → 전체 score 0에 수렴
- "옛스러운" / "old-fashioned"만 미세하게 반응 (인쇄기의 빈티지 느낌)
- 분위기 미션 평가는 해당 분위기에 맞는 이미지로 별도 테스트 필요

---

## 결론

### 확인된 사실
1. SigLIP2 모델 자체의 이미지-텍스트 매칭 능력은 우수 (영어 프롬프트 시 0.99)
2. **한국어 프롬프트가 성능 병목** — score가 3~4배 하락
3. 현재 임계값 0.70은 영어 프롬프트 기준으로는 적절, 한국어로는 통과 불가
4. 영어 프롬프트 시 정답/오답 분리력이 매우 높음 (gap 0.77)

### 개선 방향
- **P0**: 한국어 키워드 → 영어 descriptive 프롬프트 변환 레이어 추가
- **P1**: 랜드마크별 영어 설명 필드를 데이터에 추가
- **P2**: 분위기 미션용 이미지 데이터셋 확보 후 별도 벤치마크

### 최적 임계값 (영어 프롬프트 기준)
- 정답 score: 0.77 (descriptive) ~ 0.99 (scene)
- 최고 오답 score: 0.0001
- 안전 범위: **0.01 ~ 0.76**
- 현재 설정(0.70): 적정 (영어 전환 전제 하에)
