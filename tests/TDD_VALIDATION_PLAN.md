# PAZULE TDD 검증 플랜

> 리팩터링 완료 후 코드베이스의 동작 정확성을 검증하기 위한 TDD 사이클 계획.  
> 기준선 커버리지: **42%** (126개 테스트 전체 통과, 2026-04-17 측정)

---

## 현재 커버리지 스냅샷

| 모듈 | 현재 커버리지 | 목표 | 우선순위 |
|------|:----------:|:----:|:------:|
| `app/core/config/` | 95–100% | 100% | 🟢 완료 |
| `app/council/nodes.py` | 82% | 90% | 🟡 보완 |
| `app/council/graph.py` | 92% | 90% | 🟢 완료 |
| `app/metadata/validator.py` | 100% | 100% | 🟢 완료 |
| `app/services/coupon_service.py` | 84% | 90% | 🟡 보완 |
| **`app/api/routes.py`** | **0%** | **80%** | 🔴 긴급 |
| **`app/services/answer_service.py`** | **0%** | **80%** | 🔴 긴급 |
| `app/services/mission_session_service.py` | 28% | 80% | 🔴 긴급 |
| `app/council/judges.py` | 32% | 90% | 🔴 핵심 로직 |
| `app/council/aggregator.py` | 35% | 90% | 🔴 핵심 로직 |
| `app/council/deliberation.py` | 36% | 80% | 🟡 보완 |
| `app/metadata/metadata.py` | 21% | 70% | 🟡 보완 |
| `app/models/` (blip, siglip2 등) | 0% | 70% | 🟠 모킹 필요 |
| `app/prompts/` | 0% | 70% | 🟠 |
| `app/legacy/` | ~0% | 제외 | ⚪ 무시 |

**목표 총 커버리지: 80%** (핵심 비즈니스 로직 100%)

---

## TDD 사이클 원칙

```
🔴 RED      → 실패하는 테스트를 먼저 작성
🟢 GREEN    → 테스트를 통과하는 최소 코드 확인
🔵 REFACTOR → 테스트 유지하면서 코드 개선
```

> 리팩터링 검증 맥락에서 RED는 "이 동작이 테스트되지 않았음"을 확인하고,
> GREEN은 "기존 구현이 올바름"을 증명한다.

---

## Phase 1 — Config 중앙화 검증 (현재 95–100%)

**상태:** 대부분 완료. `settings.py` 3개 라인만 미커버.

### 추가할 테스트 (`tests/core/test_settings.py`)

#### 🔴 RED: 작성할 테스트 케이스

```python
class TestEnvironmentProfile:
    """environments.py get_profile() 동작 검증."""

    def test_unknown_env_falls_back_to_production(self):
        """알 수 없는 환경 이름은 production 프로필로 폴백한다."""
        profile = get_profile("nonexistent")
        assert profile["SKIP_METADATA_VALIDATION"] is False
        assert profile["BYPASS_MODEL_VALIDATION"] is False

    def test_development_enables_both_bypass_flags(self):
        """development 프로필은 두 bypass 플래그를 True로 설정한다."""
        profile = get_profile("development")
        assert profile["SKIP_METADATA_VALIDATION"] is True
        assert profile["BYPASS_MODEL_VALIDATION"] is True

    def test_test_profile_disables_all_bypass_flags(self):
        """test 프로필은 두 bypass 플래그를 False로 설정한다 (mock 활성화)."""
        profile = get_profile("test")
        assert profile["SKIP_METADATA_VALIDATION"] is False
        assert profile["BYPASS_MODEL_VALIDATION"] is False


class TestSettingsEnvPriority:
    """settings._env_or_profile(): .env > profile 우선순위 검증."""

    def test_env_var_overrides_profile(self, monkeypatch):
        """os.environ이 설정되면 profile 값보다 우선한다."""
        monkeypatch.setenv("LOCATION_PASS_THRESHOLD", "0.99")
        # Settings 재인스턴스화 필요 → importlib.reload 또는 함수 직접 테스트

    def test_missing_env_uses_profile_value(self, monkeypatch):
        """os.environ이 없으면 profile 기본값을 사용한다."""
        monkeypatch.delenv("LOCATION_PASS_THRESHOLD", raising=False)
        # profile 값 0.70이 적용됨을 확인

    def test_test_env_forces_skip_metadata_false(self):
        """PAZULE_ENV=test일 때 SKIP_METADATA_VALIDATION은 반드시 False."""
        # conftest.py가 PAZULE_ENV=test 강제 → settings 값 직접 확인
        from app.core.config import settings
        assert settings.SKIP_METADATA_VALIDATION is False

    def test_test_env_forces_bypass_model_false(self):
        """PAZULE_ENV=test일 때 BYPASS_MODEL_VALIDATION은 반드시 False."""
        from app.core.config import settings
        assert settings.BYPASS_MODEL_VALIDATION is False
```

**커버리지 목표:** `settings.py` → 100%, `environments.py` → 100%

---

## Phase 2 — Council 핵심 로직 (현재 32–82%)

### 2-A: `judges.py` (현재 32% → 목표 100%)

**역할:** 앙상블 점수 vs 임계값 비교, 경계값 케이스 판정

#### 🔴 RED: `tests/council/test_judges.py`

```python
class TestDecisionEngine:
    """judge 노드가 올바른 판정을 내리는지 검증."""

    # Happy path
    def test_score_above_threshold_is_pass(self):
        """점수가 임계값 이상이면 success=True."""

    def test_score_below_threshold_is_fail(self):
        """점수가 임계값 미만이면 success=False."""

    # 경계값
    def test_score_exactly_at_threshold_is_pass(self):
        """점수가 임계값과 정확히 같으면 통과."""

    def test_borderline_range_triggers_council(self):
        """임계값 ± COUNCIL_BORDERLINE_MARGIN 범위는 경계값으로 분류."""

    # 미션 타입별
    def test_location_threshold_applied_for_location_mission(self):
        """location 미션은 LOCATION_PASS_THRESHOLD를 사용한다."""

    def test_atmosphere_threshold_applied_for_atmosphere_mission(self):
        """atmosphere 미션은 ATMOSPHERE_PASS_THRESHOLD를 사용한다."""

    # Gate 차단
    def test_gate_failure_overrides_score(self):
        """gate_result=fail이면 점수와 무관하게 실패 판정."""

    # 에러 케이스
    def test_missing_score_returns_fail(self):
        """앙상블 점수가 없으면 실패 처리."""
```

### 2-B: `aggregator.py` (현재 35% → 목표 90%)

**역할:** 모델 투표 가중합, 충돌 감지

#### 🔴 RED: `tests/council/test_aggregator.py`

```python
class TestEnsembleAggregation:
    """aggregator가 가중합을 올바르게 계산하는지 검증."""

    def test_location_weights_applied(self):
        """location 미션: siglip2=0.30, blip=0.70 가중치 적용."""
        votes = [
            {"model": "siglip2", "score": 1.0, "label": "match"},
            {"model": "blip", "score": 0.0, "label": "no_match"},
        ]
        result = aggregate_votes(votes, "location")
        assert pytest.approx(result["merged_score"], abs=0.01) == 0.30

    def test_atmosphere_weights_applied(self):
        """atmosphere 미션: siglip2=0.80, blip=0.20 가중치 적용."""
        votes = [
            {"model": "siglip2", "score": 1.0, "label": "match"},
            {"model": "blip", "score": 0.0, "label": "no_match"},
        ]
        result = aggregate_votes(votes, "atmosphere")
        assert pytest.approx(result["merged_score"], abs=0.01) == 0.80

    def test_unknown_model_uses_default_weight(self):
        """레지스트리에 없는 모델은 DEFAULT_MODEL_WEIGHT(0.1) 사용."""

    def test_conflict_flag_set_when_spread_exceeds_threshold(self):
        """모델 간 점수 차이가 0.35 이상이면 conflict=True."""
        votes = [
            {"model": "siglip2", "score": 0.9},
            {"model": "blip", "score": 0.5},
        ]  # diff=0.40 > ENSEMBLE_CONFLICT_THRESHOLD=0.35
        result = aggregate_votes(votes, "location")
        assert result["conflict"] is True

    def test_no_conflict_when_spread_below_threshold(self):
        """점수 차이가 0.35 미만이면 conflict=False."""

    def test_empty_votes_returns_zero_score(self):
        """투표가 없으면 merged_score=0.0."""

    def test_single_vote_returns_weighted_score(self):
        """투표 1개는 해당 모델 가중치만 적용."""
```

### 2-C: `deliberation.py` (현재 36% → 목표 80%)

**역할:** Council Tier 3 에스컬레이션 (Qwen VL API 호출)

#### 🔴 RED: `tests/council/test_deliberation.py`

```python
class TestCouncilDeliberation:
    """Council 에스컬레이션 로직 검증. 외부 API는 전부 mock."""

    def test_borderline_case_triggers_escalation(self, mocker):
        """경계값 케이스에서 Qwen VL API를 호출한다."""

    def test_non_borderline_skips_escalation(self, mocker):
        """비경계값 케이스에서는 API 호출 없이 반환한다."""

    def test_council_disabled_skips_escalation(self, mocker, monkeypatch):
        """COUNCIL_ENABLED=False이면 에스컬레이션을 건너뛴다."""
        monkeypatch.setattr(settings, "COUNCIL_ENABLED", False)

    def test_api_timeout_falls_back_gracefully(self, mocker):
        """API 타임아웃 시 폴백 결과를 반환하고 에러를 기록한다."""

    def test_escalation_result_overrides_ensemble_score(self, mocker):
        """에스컬레이션 결과가 앙상블 점수보다 우선 적용된다."""
```

---

## Phase 3 — API Routes (현재 0% → 목표 80%)

**가장 긴급한 갭.** Flask 라우트 전체가 테스트 없음.

### 🔴 RED: `tests/api/test_routes.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from app import create_app  # 또는 Flask app factory


@pytest.fixture
def client():
    """Flask 테스트 클라이언트."""
    app = create_app(testing=True)
    return app.test_client()


class TestMissionStartRoute:
    """POST /api/mission/start 엔드포인트 검증."""

    def test_returns_200_with_valid_params(self, client, mocker):
        """유효한 파라미터로 세션을 시작하면 200을 반환한다."""
        mocker.patch("app.services.mission_session_service.create_session", ...)
        mocker.patch("app.services.answer_service.get_today_answers", ...)

    def test_returns_400_when_mission_type_missing(self, client):
        """mission_type이 없으면 400 Bad Request를 반환한다."""

    def test_normalizes_photo_to_atmosphere(self, client, mocker):
        """mission_type='photo'는 내부적으로 'atmosphere'로 정규화된다."""


class TestPhotoSubmitRoute:
    """POST /api/mission/submit 엔드포인트 검증."""

    def test_returns_400_when_no_file(self, client):
        """파일 없이 요청하면 400을 반환한다."""

    def test_returns_400_when_invalid_extension(self, client):
        """허용되지 않는 확장자(.gif 등)는 400을 반환한다."""

    def test_accepts_jpg_extension(self, client, mocker):
        """.jpg 파일은 업로드를 허용한다."""
        # constants.ALLOWED_UPLOAD_EXTENSIONS를 실제로 참조하는지 검증

    def test_returns_400_when_session_expired(self, client, mocker):
        """만료된 세션에 제출하면 400을 반환한다."""

    def test_pipeline_result_included_in_response(self, client, mocker):
        """파이프라인 결과가 응답에 포함된다."""


class TestCouponRedeemRoute:
    """POST /api/coupon/redeem 엔드포인트 검증."""

    def test_valid_coupon_returns_200(self, client, mocker):
        """유효한 쿠폰 코드로 리딤하면 200을 반환한다."""

    def test_already_redeemed_returns_409(self, client, mocker):
        """이미 사용된 쿠폰은 409를 반환한다."""

    def test_invalid_coupon_returns_404(self, client, mocker):
        """존재하지 않는 쿠폰은 404를 반환한다."""


class TestHintRoute:
    """GET /get-today-hint 엔드포인트 검증."""

    def test_returns_hint_for_location_mission(self, client, mocker):
        """location 미션의 힌트를 반환한다."""

    def test_returns_hint_for_atmosphere_mission(self, client, mocker):
        """atmosphere 미션의 힌트를 반환한다."""

    def test_returns_500_when_answer_service_fails(self, client, mocker):
        """answer_service 실패 시 500을 반환한다."""
```

**파일 생성:** `tests/api/__init__.py` + `tests/api/test_routes.py`

---

## Phase 4 — Services (현재 0–84%)

### 4-A: `answer_service.py` (현재 0% → 목표 80%)

**역할:** 오늘의 미션 답안 로딩·캐싱

#### 🔴 RED: `tests/services/test_answer_service.py`

```python
class TestGetTodayAnswers:
    """get_today_answers() 동작 검증."""

    def test_returns_tuple_of_four_strings(self, mocker):
        """(answer1, answer2, hint1, hint2) 4-튜플을 반환한다."""

    def test_admin_choice_overrides_default(self, mocker):
        """admin_choice1이 있으면 랜덤 선택 대신 해당 답안을 사용한다."""

    def test_caching_returns_same_result_same_day(self, mocker):
        """같은 날 두 번 호출하면 같은 결과를 반환한다."""

    def test_cache_miss_reloads_on_different_day(self, mocker):
        """다른 날짜이면 캐시를 무효화하고 새로 로드한다."""

    def test_returns_fallback_when_json_missing(self, mocker):
        """answer.json이 없으면 폴백 답안을 반환한다."""


class TestLoadMissions:
    """load_missions1/2() 파싱 검증."""

    def test_load_missions1_returns_list_of_dicts(self, tmp_path, mocker):
        """missions1 리스트를 딕셔너리 배열로 반환한다."""

    def test_empty_json_returns_empty_list(self, tmp_path, mocker):
        """빈 JSON은 빈 리스트를 반환한다."""

    def test_malformed_json_does_not_raise(self, tmp_path, mocker):
        """잘못된 JSON은 예외를 발생시키지 않고 폴백 처리한다."""
```

### 4-B: `mission_session_service.py` (현재 28% → 목표 80%)

#### 🔴 RED: `tests/services/test_mission_session_service.py`

```python
class TestCreateSession:
    def test_returns_session_with_mission_id(self, tmp_session_service):
        """create_session()은 mission_id가 있는 딕셔너리를 반환한다."""

    def test_session_has_correct_mission_type(self, tmp_session_service):
        """생성된 세션의 mission_type이 입력값과 일치한다."""

    def test_session_initial_status_is_active(self, tmp_session_service):
        """초기 세션 상태는 'active'이다."""


class TestCanSubmit:
    def test_active_session_can_submit(self, tmp_session_service):
        """활성 세션은 제출을 허용한다."""

    def test_expired_session_cannot_submit(self, tmp_session_service, monkeypatch):
        """만료된 세션은 제출을 거부한다."""
        # TTL을 0으로 설정하거나 created_at을 과거로 조작

    def test_max_submissions_reached_cannot_submit(self, tmp_session_service):
        """최대 제출 횟수를 초과하면 거부한다."""
        # MISSION_MAX_SUBMISSIONS번 record_submission() 호출 후 확인

    def test_nonexistent_session_returns_not_found(self, tmp_session_service):
        """존재하지 않는 세션은 'session_not_found'를 반환한다."""


class TestRecordSubmission:
    def test_submission_increments_count(self, tmp_session_service):
        """제출 후 submissions 카운트가 증가한다."""

    def test_submission_stores_image_hash(self, tmp_session_service):
        """제출 시 image_hash가 세션에 저장된다."""


class TestIsDuplicateHash:
    def test_same_hash_same_user_is_duplicate(self, tmp_session_service):
        """같은 사용자가 같은 이미지 해시를 두 번 제출하면 중복이다."""

    def test_same_hash_different_user_is_not_duplicate(self, tmp_session_service):
        """다른 사용자의 같은 해시는 중복이 아니다."""

    def test_different_hash_is_not_duplicate(self, tmp_session_service):
        """다른 해시는 중복이 아니다."""


class TestHashFile:
    def test_returns_sha256_hex_string(self, tmp_path):
        """hash_file()은 64자 16진수 문자열을 반환한다."""
        f = tmp_path / "test.jpg"
        f.write_bytes(b"test content")
        result = MissionSessionService.hash_file(str(f))
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_file_same_hash(self, tmp_path):
        """동일한 파일은 항상 같은 해시를 반환한다."""

    def test_different_content_different_hash(self, tmp_path):
        """다른 내용의 파일은 다른 해시를 반환한다."""
```

---

## Phase 5 — Models & Prompts (현재 0% → 목표 70%)

**전략:** 실제 모델 로드 없이 mock으로 인터페이스 검증.

### 🔴 RED: `tests/models/test_model_interfaces.py`

```python
class TestModelRegistry:
    """model_registry.get_model() 팩토리 함수 검증."""

    def test_get_siglip2_returns_siglip2_instance(self, mocker):
        """'siglip2' 요청 시 SigLIP2Model 인스턴스를 반환한다."""
        mocker.patch("app.models.siglip2.SigLIP2Model._load_model")
        model = get_model("siglip2")
        assert isinstance(model, SigLIP2Model)

    def test_get_blip_returns_blip_instance(self, mocker):
        """'blip' 요청 시 BLIPModel 인스턴스를 반환한다."""

    def test_unknown_model_raises_value_error(self):
        """알 수 없는 모델 이름은 ValueError를 발생시킨다."""

    def test_same_model_cached(self, mocker):
        """같은 모델을 두 번 요청하면 동일한 인스턴스를 반환한다 (싱글톤)."""


class TestPromptsMiddleware:
    """build_prompt_bundle() 인터페이스 검증."""

    def test_returns_dict_with_prompt_key(self, mocker):
        """반환값에 'prompt' 키가 있다."""

    def test_mission_type_injected_into_bundle(self, mocker):
        """mission_type이 프롬프트 번들에 주입된다."""

    def test_answer_injected_into_bundle(self, mocker):
        """answer가 프롬프트 번들에 주입된다."""
```

---

## Phase 6 — Metadata (현재 21% → 목표 70%)

### 🔴 RED: `tests/metadata/test_metadata_extraction.py`

```python
class TestMetadataExtraction:
    """metadata.py EXIF 추출 검증. 실제 이미지 파일 사용."""

    @pytest.fixture
    def jpeg_with_gps(self, tmp_path):
        """GPS EXIF가 포함된 JPEG 파일 생성."""
        # piexif로 GPS 태그 삽입한 테스트 이미지

    def test_extracts_gps_from_jpeg_with_exif(self, jpeg_with_gps):
        """GPS EXIF가 있는 JPEG에서 위도·경도를 추출한다."""

    def test_returns_none_gps_when_no_exif(self, tmp_path):
        """EXIF 없는 이미지는 GPS=None을 반환한다."""

    def test_extracts_date_taken(self, jpeg_with_gps):
        """촬영 날짜를 올바르게 파싱한다."""

    def test_non_image_file_does_not_raise(self, tmp_path):
        """이미지가 아닌 파일은 예외 없이 None을 반환한다."""
```

---

## pytest 설정 추가 (`pyproject.toml`)

현재 pytest 설정이 없음. 다음을 추가한다:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "unit: 빠른 단위 테스트 (I/O 없음, 외부 호출 없음)",
    "integration: 통합 테스트 (서비스 레이어 포함)",
    "slow: 느린 테스트 (실제 파일 I/O, 대형 픽스처)",
]

[tool.coverage.run]
source = ["app"]
omit = [
    "app/legacy/*",
    "*/tests/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

## 실행 명령어

```bash
# 전체 테스트 실행
uv run pytest tests/ -v

# 커버리지 포함 실행
uv run pytest tests/ --cov=app --cov-report=term-missing

# 특정 Phase만 실행
uv run pytest tests/council/ -v               # Phase 2
uv run pytest tests/api/ -v                   # Phase 3
uv run pytest tests/services/ -v              # Phase 4

# 빠른 단위 테스트만
uv run pytest tests/ -m unit -v

# 실패 즉시 중단
uv run pytest tests/ -x --tb=short
```

---

## 작업 순서 요약

| 순서 | Phase | 파일 생성 | 커버리지 기대치 |
|:----:|-------|---------|:----------:|
| 1 | Config 보완 | `tests/core/test_settings.py` | config 100% |
| 2 | judges.py | `tests/council/test_judges.py` | judges 90%+ |
| 3 | aggregator.py | `tests/council/test_aggregator.py` | aggregator 90%+ |
| 4 | API routes | `tests/api/test_routes.py` | routes 80%+ |
| 5 | answer_service | `tests/services/test_answer_service.py` | service 80%+ |
| 6 | session_service | `tests/services/test_mission_session_service.py` | session 80%+ |
| 7 | deliberation | `tests/council/test_deliberation.py` | deliberation 80%+ |
| 8 | Models & Prompts | `tests/models/test_model_interfaces.py` | models 70%+ |
| 9 | Metadata | `tests/metadata/test_metadata_extraction.py` | metadata 70%+ |
| 10 | pytest config | `pyproject.toml` 추가 | coverage 80% 강제 |

**예상 최종 커버리지: 80%+** (현재 42% → +38%p)
