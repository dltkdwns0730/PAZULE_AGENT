"""Phase 4 리팩터 검증: nodes.py에서 분리된 헬퍼 함수 단위 테스트.

리팩터 목적: validator(87L)·evaluator(107L)를 작은 헬퍼들로 분리해 단독 테스트 가능하게 함.
검증 대상:
  - _check_image_presence: 이미지 경로 유무 확인
  - _check_metadata: SKIP_METADATA_VALIDATION 플래그 반영
  - _check_duplicate: 이미지 해시 중복 검사
  - _build_bypass_votes: BYPASS_MODEL_VALIDATION 전용 가짜 투표 생성
  - _process_model_future: Future 결과 처리 및 타임아웃/에러 처리
  - _normalize_mission_type: 미션 타입 정규화
"""

from __future__ import annotations

import concurrent.futures
from typing import Any
from unittest.mock import patch

import pytest

from app.core.utils import normalize_mission_type
from app.council.nodes import (
    _build_bypass_votes,
    _check_duplicate,
    _check_image_presence,
    _check_metadata,
    _process_model_future,
)


# ── _normalize_mission_type ──────────────────────────────────────────────────


class TestNormalizeMissionType:
    def test_location_unchanged(self) -> None:
        assert normalize_mission_type("location") == "location"

    def test_atmosphere_unchanged(self) -> None:
        assert normalize_mission_type("atmosphere") == "atmosphere"

    def test_photo_becomes_atmosphere(self) -> None:
        """'photo'는 레거시 표현 → 'atmosphere'로 정규화."""
        assert normalize_mission_type("photo") == "atmosphere"

    def test_unknown_falls_back_to_location(self) -> None:
        assert normalize_mission_type("unknown") == "location"

    def test_empty_string_falls_back_to_location(self) -> None:
        assert normalize_mission_type("") == "location"


# ── _check_image_presence ────────────────────────────────────────────────────


class TestCheckImagePresence:
    """_check_image_presence 헬퍼 단위 테스트."""

    def _make_state(self) -> tuple[dict, list, dict]:
        artifacts: dict[str, Any] = {}
        errors: list[dict[str, Any]] = []
        control_flags: dict[str, Any] = {}
        return artifacts, errors, control_flags

    def test_valid_path_returns_true(self) -> None:
        artifacts, errors, flags = self._make_state()
        result = _check_image_presence("/some/real.jpg", artifacts, errors, flags)
        assert result is True

    def test_valid_path_no_errors(self) -> None:
        artifacts, errors, flags = self._make_state()
        _check_image_presence("/some/real.jpg", artifacts, errors, flags)
        assert errors == []

    def test_valid_path_no_terminate_flag(self) -> None:
        artifacts, errors, flags = self._make_state()
        _check_image_presence("/some/real.jpg", artifacts, errors, flags)
        assert flags.get("terminate") is None

    def test_none_path_returns_false(self) -> None:
        artifacts, errors, flags = self._make_state()
        result = _check_image_presence(None, artifacts, errors, flags)
        assert result is False

    def test_none_path_sets_terminate_flag(self) -> None:
        artifacts, errors, flags = self._make_state()
        _check_image_presence(None, artifacts, errors, flags)
        assert flags.get("terminate") is True

    def test_none_path_adds_error(self) -> None:
        artifacts, errors, flags = self._make_state()
        _check_image_presence(None, artifacts, errors, flags)
        assert len(errors) == 1
        assert errors[0]["code"] == "MISSING_IMAGE"

    def test_none_path_sets_gate_result_failed(self) -> None:
        artifacts, errors, flags = self._make_state()
        _check_image_presence(None, artifacts, errors, flags)
        assert artifacts["gate_result"]["passed"] is False

    def test_empty_string_path_returns_false(self) -> None:
        """빈 문자열도 image_path 없음으로 처리."""
        artifacts, errors, flags = self._make_state()
        result = _check_image_presence("", artifacts, errors, flags)
        assert result is False


# ── _check_metadata ──────────────────────────────────────────────────────────


class TestCheckMetadata:
    """_check_metadata 헬퍼 단위 테스트."""

    def test_skip_flag_returns_true(self) -> None:
        """SKIP_METADATA_VALIDATION=True면 항상 통과."""
        artifacts: dict[str, Any] = {}
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.SKIP_METADATA_VALIDATION = True
            result = _check_metadata("/fake.jpg", artifacts)
        assert result is True

    def test_skip_flag_marks_artifacts(self) -> None:
        artifacts: dict[str, Any] = {}
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.SKIP_METADATA_VALIDATION = True
            _check_metadata("/fake.jpg", artifacts)
        assert artifacts.get("metadata_check_skipped") is True

    def test_no_skip_delegates_to_validate_metadata_true(self) -> None:
        """SKIP=False일 때 validate_metadata가 True → True 반환."""
        artifacts: dict[str, Any] = {}
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.validate_metadata", return_value=True) as mock_val,
        ):
            mock_settings.SKIP_METADATA_VALIDATION = False
            result = _check_metadata("/real.jpg", artifacts)
        assert result is True
        mock_val.assert_called_once_with("/real.jpg")

    def test_no_skip_delegates_to_validate_metadata_false(self) -> None:
        """SKIP=False일 때 validate_metadata가 False → False 반환."""
        artifacts: dict[str, Any] = {}
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.validate_metadata", return_value=False),
        ):
            mock_settings.SKIP_METADATA_VALIDATION = False
            result = _check_metadata("/bad.jpg", artifacts)
        assert result is False

    def test_no_skip_marks_metadata_not_skipped(self) -> None:
        artifacts: dict[str, Any] = {}
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.validate_metadata", return_value=True),
        ):
            mock_settings.SKIP_METADATA_VALIDATION = False
            _check_metadata("/real.jpg", artifacts)
        assert artifacts.get("metadata_check_skipped") is False


# ── _check_duplicate ─────────────────────────────────────────────────────────


class TestCheckDuplicate:
    """_check_duplicate 헬퍼 단위 테스트."""

    def test_no_duplicate_returns_false(self) -> None:
        request_context: dict[str, Any] = {}
        with (
            patch("app.council.nodes.mission_session_service") as mock_svc,
            patch("app.council.nodes.settings") as mock_settings,
        ):
            mock_svc.hash_file.return_value = "abc123"
            mock_svc.is_duplicate_hash_for_user.return_value = False
            mock_settings.SKIP_METADATA_VALIDATION = False
            _, is_dup = _check_duplicate("user1", "/img.jpg", request_context)
        assert is_dup is False

    def test_duplicate_returns_true(self) -> None:
        request_context: dict[str, Any] = {}
        with (
            patch("app.council.nodes.mission_session_service") as mock_svc,
            patch("app.council.nodes.settings") as mock_settings,
        ):
            mock_svc.hash_file.return_value = "abc123"
            mock_svc.is_duplicate_hash_for_user.return_value = True
            mock_settings.SKIP_METADATA_VALIDATION = False
            _, is_dup = _check_duplicate("user1", "/img.jpg", request_context)
        assert is_dup is True

    def test_image_hash_stored_in_context(self) -> None:
        request_context: dict[str, Any] = {}
        with (
            patch("app.council.nodes.mission_session_service") as mock_svc,
            patch("app.council.nodes.settings") as mock_settings,
        ):
            mock_svc.hash_file.return_value = "deadbeef123"
            mock_svc.is_duplicate_hash_for_user.return_value = False
            mock_settings.SKIP_METADATA_VALIDATION = False
            image_hash, _ = _check_duplicate("user1", "/img.jpg", request_context)
        assert image_hash == "deadbeef123"
        assert request_context["image_hash"] == "deadbeef123"

    def test_skip_flag_ignores_duplicate(self) -> None:
        """SKIP_METADATA_VALIDATION=True면 중복이어도 False로 처리."""
        request_context: dict[str, Any] = {}
        with (
            patch("app.council.nodes.mission_session_service") as mock_svc,
            patch("app.council.nodes.settings") as mock_settings,
        ):
            mock_svc.hash_file.return_value = "abc"
            mock_svc.is_duplicate_hash_for_user.return_value = True
            mock_settings.SKIP_METADATA_VALIDATION = True
            _, is_dup = _check_duplicate("user1", "/img.jpg", request_context)
        assert is_dup is False


# ── _build_bypass_votes ──────────────────────────────────────────────────────


class TestBuildBypassVotes:
    """_build_bypass_votes 헬퍼 단위 테스트."""

    def test_returns_list(self) -> None:
        result = _build_bypass_votes(["siglip2"])
        assert isinstance(result, list)

    def test_one_model_one_vote(self) -> None:
        result = _build_bypass_votes(["siglip2"])
        assert len(result) == 1

    def test_two_models_two_votes(self) -> None:
        result = _build_bypass_votes(["siglip2", "blip"])
        assert len(result) == 2

    def test_score_is_one(self) -> None:
        result = _build_bypass_votes(["siglip2"])
        assert result[0]["score"] == 1.0

    def test_label_is_match(self) -> None:
        result = _build_bypass_votes(["blip"])
        assert result[0]["label"] == "match"

    def test_reason_contains_bypass(self) -> None:
        result = _build_bypass_votes(["siglip2"])
        assert "bypass" in result[0]["reason"].lower()

    def test_model_name_preserved(self) -> None:
        result = _build_bypass_votes(["siglip2", "blip"])
        model_names = {v["model"] for v in result}
        assert model_names == {"siglip2", "blip"}

    def test_empty_list_returns_empty(self) -> None:
        result = _build_bypass_votes([])
        assert result == []


# ── _process_model_future ────────────────────────────────────────────────────


class TestProcessModelFuture:
    """_process_model_future 헬퍼 단위 테스트."""

    def _make_future(
        self, result: Any = None, exc: Exception | None = None
    ) -> concurrent.futures.Future:
        fut: concurrent.futures.Future = concurrent.futures.Future()
        if exc:
            fut.set_exception(exc)
        else:
            fut.set_result(result)
        return fut

    def test_success_returns_vote(self) -> None:
        vote = {"model": "siglip2", "score": 0.9, "label": "match"}
        fut = self._make_future(result=vote)
        errors: list = []
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.constants") as mock_constants,
        ):
            mock_settings.API_TIMEOUT_SECONDS = 30
            mock_constants.MODEL_TIMEOUT_BUFFER_SECONDS = 5.0
            result = _process_model_future(fut, "siglip2", errors)
        assert result == vote
        assert errors == []

    def test_timeout_returns_none(self) -> None:
        fut: concurrent.futures.Future = concurrent.futures.Future()
        # Future never set → will timeout
        errors: list = []
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.constants") as mock_constants,
        ):
            mock_settings.API_TIMEOUT_SECONDS = 0
            mock_constants.MODEL_TIMEOUT_BUFFER_SECONDS = 0.01
            result = _process_model_future(fut, "siglip2", errors)
        assert result is None
        assert any(e["code"] == "MODEL_TIMEOUT" for e in errors)

    def test_exception_returns_none(self) -> None:
        fut = self._make_future(exc=RuntimeError("model crashed"))
        errors: list = []
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.constants") as mock_constants,
        ):
            mock_settings.API_TIMEOUT_SECONDS = 30
            mock_constants.MODEL_TIMEOUT_BUFFER_SECONDS = 5.0
            result = _process_model_future(fut, "blip", errors)
        assert result is None
        assert any(e["code"] == "MODEL_FAILURE" for e in errors)

    def test_error_contains_model_name(self) -> None:
        fut = self._make_future(exc=ValueError("bad"))
        errors: list = []
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.constants") as mock_constants,
        ):
            mock_settings.API_TIMEOUT_SECONDS = 30
            mock_constants.MODEL_TIMEOUT_BUFFER_SECONDS = 5.0
            _process_model_future(fut, "blip", errors)
        assert errors[0].get("model") == "blip"

    def test_timeout_uses_constants_buffer(self) -> None:
        """타임아웃 = API_TIMEOUT_SECONDS + MODEL_TIMEOUT_BUFFER_SECONDS 검증."""
        vote = {"model": "siglip2", "score": 0.9}
        fut = self._make_future(result=vote)
        errors: list = []
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.constants") as mock_constants,
        ):
            mock_settings.API_TIMEOUT_SECONDS = 10
            mock_constants.MODEL_TIMEOUT_BUFFER_SECONDS = 5.0
            # future.result를 spy해서 timeout 값을 검증
            original_result = fut.result
            captured_timeout = []

            def spy_result(timeout=None):
                captured_timeout.append(timeout)
                return original_result(timeout=999)  # 실제로는 빠르게 반환

            fut.result = spy_result
            _process_model_future(fut, "siglip2", errors)
        assert captured_timeout[0] == pytest.approx(15.0)
