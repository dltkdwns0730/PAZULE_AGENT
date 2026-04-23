# 🛠️ PAZULE Scripts

이 디렉토리는 개발 및 운영 과정에서 필요한 수동 도구, 디버깅 스크립트, 그리고 모델 성능 측정을 위한 벤치마크 도구들을 포함합니다. 모든 스크립트는 프로젝트 루트에서 `PYTHONPATH="."` 설정을 포함하여 실행해야 합니다.

---

## 📂 폴더 구조 및 주요 스크립트

### 1. [tools/](./tools) - 데이터 및 에셋 관리 도구
에셋 정리, 자동 라벨링, 정답지(GT) 생성 등 데이터 파이프라인 관련 도구입니다.

| 스크립트 | 설명 |
| :--- | :--- |
| `rename_assets.py` | `data/assets` 내의 파일명을 `{영문접두사}_{번호}` 형식으로 통일하고 중복 폴더를 병합합니다. |
| `update_atmosphere_ground_truth.py` | SigLIP2 모델을 사용하여 에셋의 분위기를 자동 분석하고 GT(JSON)를 갱신합니다. (단색 이미지 필터링 포함) |
| `generate_atmosphere_report.py` | 갱신된 분위기 라벨링 결과를 브라우저에서 확인할 수 있는 HTML 리포트를 생성합니다. |
| `unit_test_reset.py` | 테스트용 임시 데이터와 세션을 초기화합니다. |

### 2. [debug/](./debug) - 로직 시뮬레이션 및 디버깅
개별 컴포넌트나 비즈니스 로직의 동작을 격리하여 테스트합니다.

| 스크립트 | 설명 |
| :--- | :--- |
| `simulate_atmosphere_feedback.py` | 분위기 미션 제출 시 점수에 따른 성공/실패 판정 및 **대비 분석 기반 힌트** 생성을 시뮬레이션합니다. |
| `test_council_only.py` | 앙상블 점수 충돌 시 발생하는 Council(교차 검증) 기능만 단독으로 테스트합니다. |
| `debug_coupon_flow.py` | 미션 성공 후 쿠폰이 발급되고 저장되는 전 과정을 디버깅합니다. |

### 3. [benchmarks/](./benchmarks) - 모델 성능 측정
AI 모델의 정확도와 속도를 측정하여 임계값(Threshold) 설정의 근거를 마련합니다.

| 스크립트 | 설명 |
| :--- | :--- |
| `benchmark_atmosphere.py` | 현재 설정된 분위기 클러스터별 모델 점수 분포와 정확도를 측정합니다. |
| `benchmark_siglip.py` | SigLIP2 모델의 Zero-shot 성능을 단독으로 벤치마킹합니다. |

---

## 🚀 실행 방법 (Usage)

윈도우(PowerShell) 기준, 프로젝트 루트 디렉토리에서 아래와 같이 실행합니다.

```powershell
# 1. 에셋 파일명 정리
python scripts/tools/rename_assets.py

# 2. 분위기 Ground Truth 갱신 (GPU 필요)
$env:PYTHONPATH="."; python scripts/tools/update_atmosphere_ground_truth.py

# 3. 검증 리포트 생성
python scripts/tools/generate_atmosphere_report.py
```

---

## ⚠️ 주의사항
- **모델 로딩**: `tools` 및 `benchmarks` 스크립트는 실제 AI 모델(SigLIP2 등)을 로딩하므로 충분한 VRAM이 필요합니다.
- **경로**: 반드시 프로젝트 루트(`PAZULE/`)에서 실행하세요. 스크립트 폴더 내부로 들어가서 실행하면 경로 오류가 발생할 수 있습니다.
