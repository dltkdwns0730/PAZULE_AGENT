# SigLIP2 Benchmark — v2 English Prompts

> **분류**: 벤치마크 · **버전**: v2 · **최종 수정**: 2026-04-07
>
> 모델: `google/siglip2-base-patch16-224` · 장비: CPU (torch 2.10.0, transformers 5.2.0)
> 이미지: `front/src/assets/intro5.jpg` (활판공방 인쇄기)

## 목적

v1 baseline에서 확인된 한국어 프롬프트 병목을 영어 descriptive 프롬프트로 해결한 결과 검증.

---

## 변경 사항

- `app/models/prompts.py`: `LANDMARK_EN`, `ATMOSPHERE_EN` 매핑 추가
- `app/models/siglip2.py`: `prompt_bundle`의 영어 후보 텍스트 사용, `AutoProcessor` → `AutoImageProcessor` + `GemmaTokenizerFast` 분리 로딩

---

## Test 1: Location 미션 (영어 프롬프트)

프롬프트 형식: `"a photo of {english descriptive}"`

| 랜드마크 | v1 Score (KR) | v2 Score (EN) | 판정 (threshold 0.70) |
|---|---|---|---|
| **활판공방 인쇄기 (정답)** | **0.2838** | **0.9406** | **PASS** |
| 활돌이 | 0.0013 | 0.0000 | FAIL |
| 마법천자문 손오공 | 0.0003 | 0.0000 | FAIL |
| 나남출판사 | 0.0003 | 0.0000 | FAIL |
| 지혜의숲 조각상 | 0.0001 | 0.0000 | FAIL |
| 지혜의숲 고양이 | 0.0000 | 0.0000 | FAIL |
| 지혜의숲 입구 조각상 | 0.0001 | 0.0000 | FAIL |
| 네모탑 | 0.0009 | 0.0000 | FAIL |
| 창틀 피노키오 | 0.0000 | 0.0000 | FAIL |
| 피노지움 조각상 | 0.0001 | 0.0000 | FAIL |
| 로드킬 부엉이 | 0.0000 | 0.0000 | FAIL |

---

## v1 → v2 비교

| 지표 | v1 (한국어) | v2 (영어) | 변화 |
|---|---|---|---|
| 정답 score | 0.2838 | 0.9406 | **+231%** |
| 최고 오답 score | 0.0013 | 0.0000 | 개선 |
| 정답-오답 gap | 0.28 | 0.94 | **+236%** |
| 임계값(0.70) 통과 | FAIL | PASS | 해결 |
| False Positive | 0 | 0 | 유지 |

---

## 결론

1. 영어 descriptive 프롬프트 전환으로 정답 score가 0.28 → 0.94로 **3.3배 향상**
2. 오답 score는 전부 0.0000으로 **분리력 극대화**
3. 임계값 0.70을 안정적으로 통과 — FALSE NEGATIVE 문제 해결
4. `AutoProcessor` → `AutoImageProcessor` + `GemmaTokenizerFast` 분리 로딩으로 transformers 5.2.0 호환성 확보

### 적용된 영어 프롬프트 예시

| 한국어 | 영어 |
|---|---|
| 활판공방 인쇄기 | an outdoor sculpture of a vintage printing press covered in metal type blocks |
| 활돌이 | a pink cartoon character mascot statue |
| 옛스러운 | old-fashioned and vintage |
| 차분한 | calm and peaceful |
