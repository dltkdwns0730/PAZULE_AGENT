"""Council deliberation 노드 단위 테스트: council().

공공 환경 호환 설계:
  - tiered_evaluate() 자체를 mock → Judge 계층 전체 격리
  - settings.COUNCIL_ENABLED 플래그 mock
  - 파이프라인 state dict 패턴 직접 사용

검증 대상:
  - COUNCIL_ENABLED=False → 패스스루 (council_verdict 없음)
  - COUNCIL_ENABLED=True → tiered_evaluate 호출 후 council_verdict 저장
  - council_verdict 내용이 state["artifacts"]에 정확히 반영됨
  - messages 필드에 tier/approved 정보 포함
  - 빈 state 방어 처리
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from app.council.deliberation import council


# ── 헬퍼 ────────────────────────────────────────────────────────────────────

_FAKE_VERDICT = {
    "approved": True,
    "confidence": 0.9,
    "reason": "All fields consistent (Pass)",
    "escalated": False,
    "tier_reached": 1,
    "votes": [{"judge": "ConsistencyJudge", "approved": True, "reason": "OK"}],
}


def _make_state(
    merged_score: float = 0.85,
    threshold: float = 0.7,
    merged_label: str = "match",
    conflict: bool = False,
    mission_type: str = "location",
    model_votes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if model_votes is None:
        model_votes = [
            {"model": "siglip2", "score": merged_score, "label": merged_label}
        ]
    return {
        "request_context": {
            "user_id": "test_user",
            "mission_type": mission_type,
            "image_path": "fake.jpg",
            "answer": "target",
        },
        "artifacts": {
            "ensemble_result": {
                "merged_score": merged_score,
                "threshold": threshold,
                "merged_label": merged_label,
                "conflict": conflict,
            },
            "model_votes": model_votes,
        },
        "errors": [],
        "control_flags": {},
        "messages": [],
    }


def _print_council(state: dict, output: dict):
    print(f"\n{'=' * 50}")
    print("[council] EXECUTE")
    print(f"  ensemble_result={state['artifacts'].get('ensemble_result')}")
    print(f"  → council_verdict={output['artifacts'].get('council_verdict')}")
    print(f"  → messages={output.get('messages')}")
    print(f"{'=' * 50}\n")


# ── COUNCIL_ENABLED=False 패스스루 ───────────────────────────────────────────


class TestCouncilDisabled:
    """COUNCIL_ENABLED=False 일 때 패스스루 동작."""

    def _run_disabled(self, state: dict | None = None) -> dict:
        if state is None:
            state = _make_state()
        with patch("app.council.deliberation.settings") as mock_settings:
            mock_settings.COUNCIL_ENABLED = False
            return council(state)

    def test_disabled_no_council_verdict(self) -> None:
        output = self._run_disabled()
        _print_council(_make_state(), output)
        assert "council_verdict" not in output["artifacts"]

    def test_disabled_artifacts_preserved(self) -> None:
        state = _make_state()
        output = self._run_disabled(state)
        # 기존 artifacts(ensemble_result 등)은 유지
        assert "ensemble_result" in output["artifacts"]

    def test_disabled_messages_contain_passthrough(self) -> None:
        output = self._run_disabled()
        assert any("passthrough" in msg for msg in output["messages"])

    def test_disabled_returns_artifacts_key(self) -> None:
        output = self._run_disabled()
        assert "artifacts" in output

    def test_disabled_returns_messages_key(self) -> None:
        output = self._run_disabled()
        assert "messages" in output


# ── COUNCIL_ENABLED=True 정상 실행 ────────────────────────────────────────────


class TestCouncilEnabled:
    """COUNCIL_ENABLED=True 일 때 tiered_evaluate 실행 후 council_verdict 저장."""

    def _run_enabled(
        self,
        state: dict | None = None,
        verdict: dict | None = None,
    ) -> tuple[dict, dict]:
        if state is None:
            state = _make_state()
        if verdict is None:
            verdict = _FAKE_VERDICT.copy()
        with (
            patch("app.council.deliberation.settings") as mock_settings,
            patch(
                "app.council.deliberation.tiered_evaluate",
                return_value=verdict,
            ) as mock_eval,
        ):
            mock_settings.COUNCIL_ENABLED = True
            output = council(state)
        _print_council(state, output)
        return output, mock_eval

    def test_enabled_council_verdict_stored(self) -> None:
        output, _ = self._run_enabled()
        assert "council_verdict" in output["artifacts"]

    def test_enabled_verdict_matches_tiered_evaluate_return(self) -> None:
        verdict = {**_FAKE_VERDICT, "approved": False, "tier_reached": 2}
        output, _ = self._run_enabled(verdict=verdict)
        assert output["artifacts"]["council_verdict"]["approved"] is False
        assert output["artifacts"]["council_verdict"]["tier_reached"] == 2

    def test_enabled_tiered_evaluate_called_once(self) -> None:
        _, mock_eval = self._run_enabled()
        mock_eval.assert_called_once()

    def test_enabled_tiered_evaluate_receives_correct_context(self) -> None:
        state = _make_state(mission_type="atmosphere", merged_score=0.8)
        _, mock_eval = self._run_enabled(state=state)
        call_args = mock_eval.call_args[0][0]  # positional arg
        assert call_args["mission_type"] == "atmosphere"
        assert call_args["ensemble_result"]["merged_score"] == 0.8

    def test_enabled_messages_contains_tier_info(self) -> None:
        output, _ = self._run_enabled()
        assert any("tier=1" in msg for msg in output["messages"])

    def test_enabled_messages_contains_approved_info(self) -> None:
        output, _ = self._run_enabled()
        assert any("approved=True" in msg for msg in output["messages"])

    def test_enabled_existing_artifacts_preserved(self) -> None:
        state = _make_state()
        state["artifacts"]["gate_result"] = {"passed": True}
        output, _ = self._run_enabled(state=state)
        assert output["artifacts"]["gate_result"]["passed"] is True

    def test_enabled_failed_verdict_reflected(self) -> None:
        verdict = {**_FAKE_VERDICT, "approved": False, "tier_reached": 3}
        output, _ = self._run_enabled(verdict=verdict)
        assert output["artifacts"]["council_verdict"]["approved"] is False

    def test_enabled_model_votes_passed_to_context(self) -> None:
        votes = [
            {"model": "blip", "score": 0.7, "label": "match"},
            {"model": "siglip2", "score": 0.9, "label": "match"},
        ]
        state = _make_state(model_votes=votes)
        _, mock_eval = self._run_enabled(state=state)
        call_args = mock_eval.call_args[0][0]
        assert len(call_args["model_votes"]) == 2


# ── 방어 처리: 빈 state ──────────────────────────────────────────────────────


class TestCouncilEmptyState:
    """빈 또는 최소 state 입력에 대한 방어 처리."""

    def test_empty_artifacts_does_not_crash(self) -> None:
        state: dict[str, Any] = {
            "artifacts": {},
            "request_context": {},
            "errors": [],
            "messages": [],
        }
        with (
            patch("app.council.deliberation.settings") as mock_settings,
            patch(
                "app.council.deliberation.tiered_evaluate",
                return_value=_FAKE_VERDICT.copy(),
            ),
        ):
            mock_settings.COUNCIL_ENABLED = True
            output = council(state)
        assert "council_verdict" in output["artifacts"]

    def test_missing_request_context_uses_defaults(self) -> None:
        state: dict[str, Any] = {"artifacts": {}, "errors": []}
        with (
            patch("app.council.deliberation.settings") as mock_settings,
            patch(
                "app.council.deliberation.tiered_evaluate",
                return_value=_FAKE_VERDICT.copy(),
            ) as mock_eval,
        ):
            mock_settings.COUNCIL_ENABLED = True
            council(state)
        call_args = mock_eval.call_args[0][0]
        assert call_args["mission_type"] == "location"  # default fallback
