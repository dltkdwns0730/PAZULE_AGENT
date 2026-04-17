"""Phase 1 리팩터 검증: app.core.config.constants 값·타입 정확성 테스트.

리팩터 목적: 각 모듈에 하드코딩된 매직넘버를 constants.py로 중앙화.
검증 기준: 상수가 올바른 타입이며, 기존 코드에서 사용하던 값과 동일해야 한다.
"""

from __future__ import annotations

import pytest

from app.core.config import constants


# ── File Upload ─────────────────────────────────────────────────────────────


class TestAllowedUploadExtensions:
    """ALLOWED_UPLOAD_EXTENSIONS — frozenset, 5개 확장자."""

    def test_is_frozenset(self) -> None:
        assert isinstance(constants.ALLOWED_UPLOAD_EXTENSIONS, frozenset)

    def test_contains_jpg(self) -> None:
        assert ".jpg" in constants.ALLOWED_UPLOAD_EXTENSIONS

    def test_contains_jpeg(self) -> None:
        assert ".jpeg" in constants.ALLOWED_UPLOAD_EXTENSIONS

    def test_contains_png(self) -> None:
        assert ".png" in constants.ALLOWED_UPLOAD_EXTENSIONS

    def test_contains_heic(self) -> None:
        assert ".heic" in constants.ALLOWED_UPLOAD_EXTENSIONS

    def test_contains_heif(self) -> None:
        assert ".heif" in constants.ALLOWED_UPLOAD_EXTENSIONS

    def test_total_count(self) -> None:
        assert len(constants.ALLOWED_UPLOAD_EXTENSIONS) == 5

    def test_excludes_gif(self) -> None:
        assert ".gif" not in constants.ALLOWED_UPLOAD_EXTENSIONS

    def test_excludes_mp4(self) -> None:
        assert ".mp4" not in constants.ALLOWED_UPLOAD_EXTENSIONS


# ── Ensemble Model Weights ───────────────────────────────────────────────────


class TestLocationModelWeights:
    """LOCATION_MODEL_WEIGHTS — siglip2:0.60, blip:0.40."""

    def test_is_dict(self) -> None:
        assert isinstance(constants.LOCATION_MODEL_WEIGHTS, dict)

    def test_siglip2_weight(self) -> None:
        assert constants.LOCATION_MODEL_WEIGHTS["siglip2"] == pytest.approx(0.30)

    def test_blip_weight(self) -> None:
        assert constants.LOCATION_MODEL_WEIGHTS["blip"] == pytest.approx(0.70)

    def test_weights_sum_to_one(self) -> None:
        total = sum(constants.LOCATION_MODEL_WEIGHTS.values())
        assert total == pytest.approx(1.0)

    def test_has_exactly_two_models(self) -> None:
        assert len(constants.LOCATION_MODEL_WEIGHTS) == 2


class TestAtmosphereModelWeights:
    """ATMOSPHERE_MODEL_WEIGHTS — siglip2:0.75, blip:0.25."""

    def test_is_dict(self) -> None:
        assert isinstance(constants.ATMOSPHERE_MODEL_WEIGHTS, dict)

    def test_siglip2_weight(self) -> None:
        assert constants.ATMOSPHERE_MODEL_WEIGHTS["siglip2"] == pytest.approx(0.80)

    def test_blip_weight(self) -> None:
        assert constants.ATMOSPHERE_MODEL_WEIGHTS["blip"] == pytest.approx(0.20)

    def test_weights_sum_to_one(self) -> None:
        total = sum(constants.ATMOSPHERE_MODEL_WEIGHTS.values())
        assert total == pytest.approx(1.0)

    def test_location_and_atmosphere_differ(self) -> None:
        """두 미션 가중치가 서로 달라야 한다."""
        assert (
            constants.LOCATION_MODEL_WEIGHTS["siglip2"]
            != constants.ATMOSPHERE_MODEL_WEIGHTS["siglip2"]
        )


class TestDefaultModelWeight:
    """DEFAULT_MODEL_WEIGHT — 레지스트리 미등록 모델의 폴백 가중치."""

    def test_is_float(self) -> None:
        assert isinstance(constants.DEFAULT_MODEL_WEIGHT, float)

    def test_value(self) -> None:
        assert constants.DEFAULT_MODEL_WEIGHT == pytest.approx(0.1)

    def test_is_positive(self) -> None:
        assert constants.DEFAULT_MODEL_WEIGHT > 0


# ── Score Thresholds ─────────────────────────────────────────────────────────


class TestEnsembleConflictThreshold:
    """ENSEMBLE_CONFLICT_THRESHOLD — 앙상블 모델 간 충돌 감지 임계값."""

    def test_is_float(self) -> None:
        assert isinstance(constants.ENSEMBLE_CONFLICT_THRESHOLD, float)

    def test_value(self) -> None:
        assert constants.ENSEMBLE_CONFLICT_THRESHOLD == pytest.approx(0.35)

    def test_between_zero_and_one(self) -> None:
        assert 0.0 < constants.ENSEMBLE_CONFLICT_THRESHOLD < 1.0


# ── Timeout ──────────────────────────────────────────────────────────────────


class TestModelTimeoutBuffer:
    """MODEL_TIMEOUT_BUFFER_SECONDS — future.result() 타임아웃 여유 시간."""

    def test_is_float(self) -> None:
        assert isinstance(constants.MODEL_TIMEOUT_BUFFER_SECONDS, float)

    def test_value(self) -> None:
        assert constants.MODEL_TIMEOUT_BUFFER_SECONDS == pytest.approx(5.0)

    def test_is_positive(self) -> None:
        assert constants.MODEL_TIMEOUT_BUFFER_SECONDS > 0


# ── Coupon ───────────────────────────────────────────────────────────────────


class TestCouponConstants:
    """COUPON_CODE_LENGTH / DEFAULT_DISCOUNT_RULE."""

    def test_code_length_is_int(self) -> None:
        assert isinstance(constants.COUPON_CODE_LENGTH, int)

    def test_code_length_value(self) -> None:
        assert constants.COUPON_CODE_LENGTH == 8

    def test_discount_rule_is_str(self) -> None:
        assert isinstance(constants.DEFAULT_DISCOUNT_RULE, str)

    def test_discount_rule_value(self) -> None:
        assert constants.DEFAULT_DISCOUNT_RULE == "10%_OFF"

    def test_discount_rule_not_empty(self) -> None:
        assert len(constants.DEFAULT_DISCOUNT_RULE) > 0
