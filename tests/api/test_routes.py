import pytest
from flask import Flask
from unittest.mock import patch
from app.api.routes import api


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


class TestHintRoute:
    """GET /get-today-hint 엔드포인트 검증."""

    def test_get_hint_location_success(self, client):
        """location 미션 힌트 요청 시 200과 정답/힌트를 반환한다."""
        mock_answers = ("ans1", "ans2", "hint1", "hint2", "vqa1", "vqa2")
        with patch("app.api.routes.get_today_answers", return_value=mock_answers):
            response = client.get("/get-today-hint?mission_type=location")
            data = response.get_json()

            assert response.status_code == 200
            assert data["answer"] == "ans1"
            assert data["hint"] == "hint1"

    def test_get_hint_atmosphere_success(self, client):
        """atmosphere 미션 힌트 요청 시 ans2/hint2를 반환한다."""
        mock_answers = ("ans1", "ans2", "hint1", "hint2", "vqa1", "vqa2")
        with patch("app.api.routes.get_today_answers", return_value=mock_answers):
            response = client.get("/get-today-hint?mission_type=atmosphere")
            data = response.get_json()

            assert response.status_code == 200
            assert data["answer"] == "ans2"
            assert data["hint"] == "hint2"

    def test_get_hint_error_500(self, client):
        """내부 에러 발생 시 500을 반환한다."""
        with patch(
            "app.api.routes.get_today_answers", side_effect=Exception("DB Error")
        ):
            response = client.get("/get-today-hint")
            assert response.status_code == 500
            assert "DB Error" in response.get_json()["error"]


class TestMissionStartRoute:
    """POST /api/mission/start 엔드포인트 검증."""

    def test_mission_start_success(self, client):
        """세션 생성 성공 시 200과 세션 정보를 반환한다."""
        mock_answers = ("ans1", "ans2", "hint1", "hint2", "vqa1", "vqa2")
        mock_session = {
            "mission_id": "test_id",
            "mission_type": "location",
            "max_submissions": 3,
            "expires_at": "2026-04-22",
            "user_id": "guest",
            "site_id": "default",
            "answer": "ans1",
            "hint": "hint1",
        }

        with patch(
            "app.api.routes.get_today_answers", return_value=mock_answers
        ), patch(
            "app.api.routes.mission_session_service.create_session",
            return_value=mock_session,
        ):
            payload = {"mission_type": "location", "user_id": "test_user"}
            response = client.post("/api/mission/start", json=payload)
            data = response.get_json()

            assert response.status_code == 200
            assert data["mission_id"] == "test_id"
            assert data["hint"] == "hint1"
            # legacy format check (atmosphere -> photo 등)
            assert data["mission_type"] == "location"


class TestCouponRedeemRoute:
    """POST /api/coupon/redeem 엔드포인트 검증."""

    def test_redeem_success(self, client):
        """쿠폰 사용 성공 시 200을 반환한다."""
        mock_result = {"redeem_status": "redeemed", "message": "Success"}
        with patch(
            "app.api.routes.coupon_service.redeem_coupon", return_value=mock_result
        ):
            payload = {"coupon_code": "ABC-123", "partner_pos_id": "POS-01"}
            response = client.post("/api/coupon/redeem", json=payload)

            assert response.status_code == 200
            assert response.get_json()["redeem_status"] == "redeemed"

    def test_redeem_fail_already_used(self, client):
        """이미 사용된 쿠폰은 400(또는 로직에 따른 코드)을 반환한다."""
        mock_result = {"redeem_status": "already_redeemed", "message": "Already used"}
        with patch(
            "app.api.routes.coupon_service.redeem_coupon", return_value=mock_result
        ):
            payload = {"coupon_code": "USED-01", "partner_pos_id": "POS-01"}
            response = client.post("/api/coupon/redeem", json=payload)

            assert response.status_code == 400
            assert response.get_json()["redeem_status"] == "already_redeemed"
