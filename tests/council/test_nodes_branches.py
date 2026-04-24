"""nodes.py 미커버 분기 전용 단위 테스트.

대상 라인:
  - 340-348 : _select_models — override 없는 경로 (location/atmosphere × ensemble/단일)
  - 370-374 : _invoke_model — ModelRegistry mock 경유 실행
  - 401-407 : evaluator — no-votes 에러 분기 (모든 모델 실패)
  - 444     : evaluator — _append_error(NO_MODEL_VOTES) 호출
  - 552-560 : judge — gate not passed → forced fail
  - 570-574 : judge — conflict + borderline → 강제 fail
  - 579-586 : judge — council_verdict override + escalated
  - 713-729 : responder — gate passed 但 success=False (fail 응답)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch


from app.council.nodes import (
    _invoke_model,
    _select_models,
    evaluator,
    judge,
    responder,
)


# ── _select_models (no override) ─────────────────────────────────────────────


class TestSelectModelsNoOverride:
    """override=None 일 때 settings 기반 모델 선택 분기."""

    def _mock_settings(
        self,
        location_mode: str = "siglip2",
        atmosphere_mode: str = "blip",
        location_ensemble: list | None = None,
        atmosphere_ensemble: list | None = None,
    ):
        m = MagicMock()
        m.MODEL_SELECTION_LOCATION = location_mode
        m.MODEL_SELECTION_ATMOSPHERE = atmosphere_mode
        m.location_ensemble_models = location_ensemble or ["siglip2", "blip"]
        m.atmosphere_ensemble_models = atmosphere_ensemble or ["siglip2", "blip"]
        return m

    def test_location_single_model(self) -> None:
        """location + 단일 모델 설정 → [mode] 반환."""
        with patch("app.council.nodes.settings", self._mock_settings("siglip2")):
            result = _select_models("location", override=None)
        assert result == ["siglip2"]

    def test_location_ensemble_mode(self) -> None:
        """location + ensemble 설정 → location_ensemble_models 반환."""
        mock = self._mock_settings(
            location_mode="ensemble", location_ensemble=["siglip2", "blip"]
        )
        with patch("app.council.nodes.settings", mock):
            result = _select_models("location", override=None)
        assert result == ["siglip2", "blip"]

    def test_atmosphere_single_model(self) -> None:
        """atmosphere + 단일 모델 설정 → [mode] 반환."""
        with patch(
            "app.council.nodes.settings", self._mock_settings(atmosphere_mode="blip")
        ):
            result = _select_models("atmosphere", override=None)
        assert result == ["blip"]

    def test_atmosphere_ensemble_mode(self) -> None:
        """atmosphere + ensemble 설정 → atmosphere_ensemble_models 반환."""
        mock = self._mock_settings(
            atmosphere_mode="ensemble",
            atmosphere_ensemble=["siglip2", "blip"],
        )
        with patch("app.council.nodes.settings", mock):
            result = _select_models("atmosphere", override=None)
        assert result == ["siglip2", "blip"]

    def test_override_single_model_ignores_settings(self) -> None:
        """override가 모델명이면 settings와 무관하게 [override] 반환."""
        with patch("app.council.nodes.settings", self._mock_settings()):
            result = _select_models("location", override="qwen")
        assert result == ["qwen"]

    def test_override_ensemble_location(self) -> None:
        """override='ensemble' + location → location_ensemble_models."""
        mock = self._mock_settings(location_ensemble=["siglip2", "blip"])
        with patch("app.council.nodes.settings", mock):
            result = _select_models("location", override="ensemble")
        assert result == ["siglip2", "blip"]

    def test_override_ensemble_atmosphere(self) -> None:
        """override='ensemble' + atmosphere → atmosphere_ensemble_models."""
        mock = self._mock_settings(atmosphere_ensemble=["siglip2"])
        with patch("app.council.nodes.settings", mock):
            result = _select_models("atmosphere", override="ensemble")
        assert result == ["siglip2"]


# ── _invoke_model ─────────────────────────────────────────────────────────────


class TestInvokeModel:
    """_invoke_model — ModelRegistry를 mock해 실행 경로를 검증한다."""

    def _make_registry(self, probe_return: dict) -> MagicMock:
        probe = MagicMock()
        probe.probe.return_value = probe_return
        registry = MagicMock()
        registry.get.return_value = probe
        return registry

    def test_calls_probe_with_correct_args(self) -> None:
        probe_return = {"model": "siglip2", "score": 0.9, "label": "match"}
        registry = self._make_registry(probe_return)
        with patch("app.models.model_registry.ModelRegistry") as mock_cls:
            mock_cls.get_instance.return_value = registry
            result = _invoke_model("siglip2", "location", "/img.jpg", "answer", {})
        registry.get.assert_called_once_with("siglip2")
        assert result == probe_return

    def test_returns_probe_output(self) -> None:
        expected = {"score": 0.75, "label": "mismatch", "reason": "low score"}
        registry = self._make_registry(expected)
        with patch("app.models.model_registry.ModelRegistry") as mock_cls:
            mock_cls.get_instance.return_value = registry
            result = _invoke_model(
                "blip", "atmosphere", "/img.jpg", "sunset", {"q": "q"}
            )
        assert result["score"] == 0.75
        assert result["label"] == "mismatch"

    def test_probe_receives_prompt_bundle(self) -> None:
        probe = MagicMock()
        probe.probe.return_value = {"score": 0.5}
        registry = MagicMock()
        registry.get.return_value = probe
        bundle = {"system": "judge this", "user": "match?"}
        with patch("app.models.model_registry.ModelRegistry") as mock_cls:
            mock_cls.get_instance.return_value = registry
            _invoke_model("blip", "location", "/img.jpg", "answer", bundle)
        probe.probe.assert_called_once_with("location", "/img.jpg", "answer", bundle)


# ── evaluator — no-votes 분기 ─────────────────────────────────────────────────


class TestEvaluatorNoVotes:
    """모든 모델 future가 실패해 votes=[] 일 때 NO_MODEL_VOTES 에러를 추가한다."""

    def _state(self, mission_type: str = "location") -> dict[str, Any]:
        return {
            "request_context": {
                "mission_type": mission_type,
                "image_path": "/img.jpg",
                "answer": "answer",
                "model_selection": "siglip2",
            },
            "artifacts": {},
            "errors": [],
        }

    def test_no_votes_appends_no_model_votes_error(self) -> None:
        state = self._state()
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.build_prompt_bundle", return_value={}),
            patch("app.council.nodes._process_model_future", return_value=None),
        ):
            mock_settings.BYPASS_MODEL_VALIDATION = False
            mock_settings.MODEL_SELECTION_LOCATION = "siglip2"
            mock_settings.location_ensemble_models = ["siglip2"]
            mock_settings.API_TIMEOUT_SECONDS = 30
            with patch(
                "app.council.nodes._invoke_model", side_effect=RuntimeError("fail")
            ):
                result = evaluator(state)
        error_codes = [e["code"] for e in result["errors"]]
        assert "NO_MODEL_VOTES" in error_codes

    def test_no_votes_model_votes_is_empty_list(self) -> None:
        state = self._state()
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.build_prompt_bundle", return_value={}),
            patch("app.council.nodes._process_model_future", return_value=None),
        ):
            mock_settings.BYPASS_MODEL_VALIDATION = False
            mock_settings.MODEL_SELECTION_LOCATION = "siglip2"
            mock_settings.location_ensemble_models = ["siglip2"]
            mock_settings.API_TIMEOUT_SECONDS = 30
            with patch(
                "app.council.nodes._invoke_model", side_effect=RuntimeError("fail")
            ):
                result = evaluator(state)
        assert result["artifacts"]["model_votes"] == []

    def test_bypass_mode_skips_model_execution(self) -> None:
        """BYPASS=True면 no-votes 에러 없이 bypass 메시지 반환."""
        state = self._state()
        with (
            patch("app.council.nodes.settings") as mock_settings,
            patch("app.council.nodes.build_prompt_bundle", return_value={}),
        ):
            mock_settings.BYPASS_MODEL_VALIDATION = True
            mock_settings.MODEL_SELECTION_LOCATION = "siglip2"
            mock_settings.location_ensemble_models = ["siglip2"]
            result = evaluator(state)
        error_codes = [e["code"] for e in result["errors"]]
        assert "NO_MODEL_VOTES" not in error_codes
        assert any("bypass" in m for m in result["messages"])


# ── judge — gate not passed ───────────────────────────────────────────────────


class TestJudgeGateBlocked:
    """gate_result.passed=False → forced fail 분기."""

    def _blocked_state(self, reason: str = "gate_blocked") -> dict[str, Any]:
        return {
            "artifacts": {
                "gate_result": {"passed": False, "reason": reason},
                "ensemble_result": {
                    "mission_type": "location",
                    "merged_score": 0.9,
                    "threshold": 0.7,
                    "conflict": False,
                },
            },
            "control_flags": {},
            "errors": [],
        }

    def test_gate_blocked_success_is_false(self) -> None:
        result = judge(self._blocked_state())
        assert result["artifacts"]["judgment"]["success"] is False

    def test_gate_blocked_reason_preserved(self) -> None:
        result = judge(self._blocked_state(reason="duplicate_image"))
        assert result["artifacts"]["judgment"]["reason"] == "duplicate_image"

    def test_gate_blocked_confidence_is_zero(self) -> None:
        result = judge(self._blocked_state())
        assert result["artifacts"]["judgment"]["confidence"] == 0.0

    def test_gate_blocked_message(self) -> None:
        result = judge(self._blocked_state())
        assert "gate blocked" in result["messages"][0]

    def test_gate_blocked_default_reason_when_missing(self) -> None:
        state = {
            "artifacts": {
                "gate_result": {"passed": False},  # reason 없음
                "ensemble_result": {},
            },
            "control_flags": {},
            "errors": [],
        }
        result = judge(state)
        assert result["artifacts"]["judgment"]["reason"] == "gate_blocked"


# ── judge — conflict 분기 ─────────────────────────────────────────────────────


class TestJudgeConflict:
    """conflict=True + borderline 이내 → 강제 fail."""

    def _conflict_state(
        self,
        score: float = 0.72,
        threshold: float = 0.70,
        conflict: bool = True,
    ) -> dict[str, Any]:
        return {
            "artifacts": {
                "gate_result": {"passed": True},
                "ensemble_result": {
                    "mission_type": "location",
                    "merged_score": score,
                    "threshold": threshold,
                    "conflict": conflict,
                },
            },
            "control_flags": {},
            "errors": [],
        }

    def test_conflict_within_borderline_overrides_to_fail(self) -> None:
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            result = judge(self._conflict_state(score=0.72, threshold=0.70))
        # borderline = 0.70 + 0.05 = 0.75 → score(0.72) < 0.75 → fail
        assert result["artifacts"]["judgment"]["success"] is False

    def test_conflict_reason_is_model_conflict(self) -> None:
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            result = judge(self._conflict_state(score=0.72, threshold=0.70))
        assert (
            result["artifacts"]["judgment"]["reason"] == "model_conflict_requires_retry"
        )

    def test_conflict_sets_manual_review_flag(self) -> None:
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            result = judge(self._conflict_state(score=0.72, threshold=0.70))
        assert result["control_flags"].get("manual_review") is True

    def test_conflict_above_borderline_does_not_override(self) -> None:
        """conflict여도 borderline 밖(score >= borderline)이면 override 없음."""
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            # borderline = 0.70 + 0.05 = 0.75 → score(0.80) >= 0.75 → override 없음
            result = judge(self._conflict_state(score=0.80, threshold=0.70))
        assert (
            result["artifacts"]["judgment"]["reason"] != "model_conflict_requires_retry"
        )

    def test_no_conflict_no_override(self) -> None:
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            result = judge(
                self._conflict_state(score=0.80, threshold=0.70, conflict=False)
            )
        assert result["artifacts"]["judgment"]["success"] is True


# ── judge — council_verdict 분기 ─────────────────────────────────────────────


class TestJudgeCouncilVerdict:
    """council_verdict 존재 시 override + escalated 분기."""

    def _verdict_state(
        self,
        council_approved: bool,
        score_success: bool,
        escalated: bool = False,
        verdict_reason: str = "council_says_so",
    ) -> dict[str, Any]:
        score = 0.80 if score_success else 0.50
        return {
            "artifacts": {
                "gate_result": {"passed": True},
                "ensemble_result": {
                    "mission_type": "location",
                    "merged_score": score,
                    "threshold": 0.70,
                    "conflict": False,
                },
                "council_verdict": {
                    "approved": council_approved,
                    "reason": verdict_reason,
                    "escalated": escalated,
                },
            },
            "control_flags": {},
            "errors": [],
        }

    def test_council_override_approved_when_score_failed(self) -> None:
        """점수 실패지만 council이 approved → success=True."""
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            result = judge(
                self._verdict_state(council_approved=True, score_success=False)
            )
        assert result["artifacts"]["judgment"]["success"] is True

    def test_council_override_rejected_when_score_passed(self) -> None:
        """점수 통과지만 council이 rejected → success=False."""
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            result = judge(
                self._verdict_state(council_approved=False, score_success=True)
            )
        assert result["artifacts"]["judgment"]["success"] is False

    def test_council_override_reason_contains_council_override(self) -> None:
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            result = judge(
                self._verdict_state(council_approved=True, score_success=False)
            )
        assert "council_override" in result["artifacts"]["judgment"]["reason"]

    def test_council_escalated_sets_manual_review(self) -> None:
        """council_verdict.escalated=True → control_flags.manual_review=True."""
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            result = judge(
                self._verdict_state(
                    council_approved=True, score_success=True, escalated=True
                )
            )
        assert result["control_flags"].get("manual_review") is True

    def test_no_escalated_no_manual_review(self) -> None:
        with patch("app.council.nodes.settings") as mock_settings:
            mock_settings.COUNCIL_BORDERLINE_MARGIN = 0.05
            result = judge(
                self._verdict_state(
                    council_approved=True, score_success=True, escalated=False
                )
            )
        assert result["control_flags"].get("manual_review") is not True


# ── responder — fail 분기 ─────────────────────────────────────────────────────


class TestResponderFail:
    """gate passed 但 judgment.success=False → encouragement 테마 실패 응답."""

    def _fail_state(
        self,
        mission_type: str = "location",
        votes: list | None = None,
        reason: str = "score_below_threshold",
        answer: str = "지혜의숲",
        static_hint: str = "책이 가득한 곳",
    ) -> dict[str, Any]:
        return {
            "request_context": {
                "mission_type": mission_type,
                "answer": answer,
                "static_hint": static_hint,
            },
            "artifacts": {
                "gate_result": {"passed": True},
                "judgment": {"success": False, "reason": reason, "confidence": 0.45},
                "coupon_decision": {"eligible": False, "deny_reason": reason},
                "ensemble_result": {"merged_score": 0.45},
                "model_votes": votes or [],
            },
            "errors": [],
        }

    def test_fail_ui_theme_is_encouragement(self) -> None:
        result = responder(self._fail_state())
        assert result["final_response"]["ui_theme"] == "encouragement"

    def test_fail_success_is_false(self) -> None:
        result = responder(self._fail_state())
        assert result["final_response"]["data"]["success"] is False

    def test_fail_message_in_response(self) -> None:
        result = responder(self._fail_state())
        assert "messages" in result
        assert result["messages"] == ["responder: fail"]

    def test_fail_hint_from_llm(self) -> None:
        """실패 시 _generate_retry_hint를 통해 LLM 힌트가 반환된다."""
        with patch(
            "app.council.nodes._generate_retry_hint",
            return_value="감성적인 힌트 문장입니다.",
        ) as mock_hint:
            result = responder(self._fail_state())
        mock_hint.assert_called_once_with("지혜의숲", "책이 가득한 곳", "location", [])
        assert result["final_response"]["data"]["hint"] == "감성적인 힌트 문장입니다."

    def test_fail_hint_llm_receives_static_hint_and_answer(self) -> None:
        """_generate_retry_hint에 answer, static_hint, mission_type이 정확히 전달된다."""
        with patch(
            "app.council.nodes._generate_retry_hint",
            return_value="힌트",
        ) as mock_hint:
            responder(
                self._fail_state(
                    answer="화사한",
                    static_hint="밝은 느낌의 사진",
                    mission_type="atmosphere",
                )
            )
        mock_hint.assert_called_once_with(
            "화사한", "밝은 느낌의 사진", "atmosphere", []
        )

    def test_fail_atmosphere_maps_to_photo_in_legacy(self) -> None:
        """atmosphere 미션은 legacy missionType='photo'로 변환."""
        result = responder(self._fail_state(mission_type="atmosphere"))
        assert result["final_response"]["data"]["missionType"] == "photo"

    def test_fail_confidence_preserved(self) -> None:
        result = responder(self._fail_state())
        assert result["final_response"]["data"]["confidence"] == 0.45
