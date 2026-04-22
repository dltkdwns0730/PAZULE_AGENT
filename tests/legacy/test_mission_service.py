"""app.legacy.mission_service 단위 테스트.

검증 대상:
  - run_mission1: BLIP 성공 → 쿠폰 발급 / BLIP 실패 → LLM 힌트
  - run_mission2: LLM 성공 → 쿠폰 발급 / LLM 실패 → 힌트
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


# ── run_mission1 ──────────────────────────────────────────────────────────────


class TestRunMission1:
    def test_success_returns_coupon(self) -> None:
        fake_coupon = {"code": "ABCD1234", "status": "issued"}
        with (
            patch(
                "app.legacy.mission_service.check_with_blip", return_value=(True, {})
            ),
            patch("app.legacy.mission_service.coupon_service") as mock_cs,
        ):
            mock_cs.issue_coupon.return_value = fake_coupon
            from app.legacy.mission_service import run_mission1

            result = run_mission1("/img.jpg", "네모탑")

        assert result["success"] is True
        assert result["coupon"] == fake_coupon

    def test_failure_returns_hint(self) -> None:
        blip_info = {"caption": "something else"}
        mock_llm = MagicMock()
        mock_llm.generate_blip_hint.return_value = "Try the north entrance."
        with (
            patch(
                "app.legacy.mission_service.check_with_blip",
                return_value=(False, blip_info),
            ),
            patch("app.legacy.mission_service.get_llm_service", return_value=mock_llm),
        ):
            from app.legacy.mission_service import run_mission1

            result = run_mission1("/img.jpg", "네모탑")

        assert result["success"] is False
        assert result["hint"] == "Try the north entrance."
        assert "message" in result


# ── run_mission2 ──────────────────────────────────────────────────────────────


class TestRunMission2:
    def test_success_returns_coupon(self) -> None:
        fake_coupon = {"code": "XY123456", "status": "issued"}
        mock_llm = MagicMock()
        mock_llm.verify_mood.return_value = {"success": True, "reason": "Great mood!"}
        with (
            patch(
                "app.legacy.mission_service.get_visual_context",
                return_value="bright scene",
            ),
            patch("app.legacy.mission_service.get_llm_service", return_value=mock_llm),
            patch("app.legacy.mission_service.coupon_service") as mock_cs,
        ):
            mock_cs.issue_coupon.return_value = fake_coupon
            from app.legacy.mission_service import run_mission2

            result = run_mission2("/img.jpg", "화사한")

        assert result["success"] is True
        assert result["coupon"] == fake_coupon
        assert result["message"] == "Great mood!"

    def test_success_uses_default_message_if_no_reason(self) -> None:
        mock_llm = MagicMock()
        mock_llm.verify_mood.return_value = {"success": True}
        with (
            patch("app.legacy.mission_service.get_visual_context", return_value="ctx"),
            patch("app.legacy.mission_service.get_llm_service", return_value=mock_llm),
            patch("app.legacy.mission_service.coupon_service") as mock_cs,
        ):
            mock_cs.issue_coupon.return_value = {"code": "AAAAAAAA"}
            from app.legacy.mission_service import run_mission2

            result = run_mission2("/img.jpg", "화사한")

        assert result["success"] is True
        assert "감성 분석 성공" in result["message"]

    def test_failure_returns_hint(self) -> None:
        mock_llm = MagicMock()
        mock_llm.verify_mood.return_value = {
            "success": False,
            "reason": "분위기가 맞지 않습니다.",
        }
        with (
            patch("app.legacy.mission_service.get_visual_context", return_value="dark"),
            patch("app.legacy.mission_service.get_llm_service", return_value=mock_llm),
        ):
            from app.legacy.mission_service import run_mission2

            result = run_mission2("/img.jpg", "활기찬")

        assert result["success"] is False
        assert result["hint"] == "분위기가 맞지 않습니다."
        assert "message" in result

    def test_failure_uses_default_hint_if_no_reason(self) -> None:
        mock_llm = MagicMock()
        mock_llm.verify_mood.return_value = {"success": False}
        with (
            patch("app.legacy.mission_service.get_visual_context", return_value="ctx"),
            patch("app.legacy.mission_service.get_llm_service", return_value=mock_llm),
        ):
            from app.legacy.mission_service import run_mission2

            result = run_mission2("/img.jpg", "활기찬")

        assert result["success"] is False
        assert isinstance(result["hint"], str)
        assert len(result["hint"]) > 0
