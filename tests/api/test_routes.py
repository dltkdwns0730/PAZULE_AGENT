import io

import pytest
from flask import Flask
from unittest.mock import patch
from app.api.user_routes import user_api as api
from app.security.auth import AuthPrincipal


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


def auth_principal(user_id: str = "guest") -> AuthPrincipal:
    return AuthPrincipal(
        user_id=user_id,
        email=f"{user_id}@example.com",
        claims={"sub": user_id},
    )


class TestHintRoute:
    """GET /get-today-hint 엔드포인트 검증."""

    def test_get_hint_location_success(self, client):
        """location 미션 힌트 요청 시 200과 정답/힌트를 반환한다."""
        mock_answers = ("ans1", "ans2", "hint1", "hint2", "vqa1", "vqa2")
        with (
            patch("app.api.user_routes.get_today_answers", return_value=mock_answers),
            patch(
                "app.api.user_routes.verify_supabase_token",
                return_value=auth_principal(),
            ),
        ):
            response = client.get(
                "/get-today-hint?mission_type=location", headers=AUTH_HEADERS
            )
            data = response.get_json()

            assert response.status_code == 200
            assert data["answer"] == "ans1"
            assert data["hint"] == "hint1"

    def test_get_hint_atmosphere_success(self, client):
        """atmosphere 미션 힌트 요청 시 ans2/hint2를 반환한다."""
        mock_answers = ("ans1", "ans2", "hint1", "hint2", "vqa1", "vqa2")
        with (
            patch("app.api.user_routes.get_today_answers", return_value=mock_answers),
            patch(
                "app.api.user_routes.verify_supabase_token",
                return_value=auth_principal(),
            ),
        ):
            response = client.get(
                "/get-today-hint?mission_type=atmosphere", headers=AUTH_HEADERS
            )
            data = response.get_json()

            assert response.status_code == 200
            assert data["answer"] == "ans2"
            assert data["hint"] == "hint2"

    def test_get_hint_error_500(self, client):
        """내부 에러 발생 시 500을 반환한다."""
        with (
            patch(
                "app.api.user_routes.get_today_answers",
                side_effect=Exception("DB Error"),
            ),
            patch(
                "app.api.user_routes.verify_supabase_token",
                return_value=auth_principal(),
            ),
        ):
            response = client.get("/get-today-hint", headers=AUTH_HEADERS)
            assert response.status_code == 500
            assert "DB Error" in response.get_json()["error"]


class TestMissionStartRoute:
    """POST /api/mission/start 엔드포인트 검증."""

    def test_mission_start_requires_auth(self, client):
        payload = {
            "mission_type": "location",
            "user_id": "spoofed-user",
            "client_lat": 37.711988,
            "client_lng": 126.6867095,
            "accuracy_meters": 20,
        }

        response = client.post("/api/mission/start", json=payload)

        assert response.status_code == 401
        assert response.get_json()["error"] == "authorization_required"

    def test_mission_start_uses_verified_supabase_user_id(self, client):
        mock_answers = ("ans1", "ans2", "hint1", "hint2", "vqa1", "vqa2")
        mock_session = {
            "mission_id": "test_id",
            "mission_type": "location",
            "max_submissions": 3,
            "expires_at": "2026-04-22",
            "user_id": "auth-user",
            "site_id": "default",
            "answer": "ans1",
            "hint": "hint1",
        }

        with (
            patch("app.api.user_routes.get_today_answers", return_value=mock_answers),
            patch(
                "app.api.user_routes.verify_supabase_token",
                return_value=auth_principal("auth-user"),
            ),
            patch(
                "app.api.user_routes.mission_session_service.create_session",
                return_value=mock_session,
            ) as create_session,
        ):
            response = client.post(
                "/api/mission/start",
                headers={"Authorization": "Bearer valid-token"},
                json={
                    "mission_type": "location",
                    "user_id": "spoofed-user",
                    "client_lat": 37.711988,
                    "client_lng": 126.6867095,
                    "accuracy_meters": 20,
                },
            )

        assert response.status_code == 200
        create_session.assert_called_once()
        assert create_session.call_args.kwargs["user_id"] == "auth-user"

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

        with (
            patch("app.api.user_routes.get_today_answers", return_value=mock_answers),
            patch(
                "app.api.user_routes.verify_supabase_token",
                return_value=auth_principal(),
            ),
            patch(
                "app.api.user_routes.mission_session_service.create_session",
                return_value=mock_session,
            ),
        ):
            payload = {
                "mission_type": "location",
                "user_id": "test_user",
                "client_lat": 37.711988,
                "client_lng": 126.6867095,
                "accuracy_meters": 20,
            }
            response = client.post(
                "/api/mission/start", json=payload, headers=AUTH_HEADERS
            )
            data = response.get_json()

            assert response.status_code == 200
            assert data["mission_id"] == "test_id"
            assert data["hint"] == "hint1"
            assert data["location_validation"]["allowed"] is True
            # legacy format check (atmosphere -> photo 등)
            assert data["mission_type"] == "location"

    def test_mission_start_demo_auth_skips_missing_gps(self, client, monkeypatch):
        monkeypatch.setattr("app.api.user_routes.settings.DEMO_AUTH_ENABLED", True)
        monkeypatch.setattr("app.api.user_routes.settings.SKIP_GPS_VALIDATION", False)
        mock_answers = ("ans1", "ans2", "hint1", "hint2", "vqa1", "vqa2")
        mock_session = {
            "mission_id": "demo-mission",
            "mission_type": "location",
            "max_submissions": 3,
            "expires_at": "2026-04-29T00:00:00Z",
            "user_id": "guest",
            "site_id": "default",
            "answer": "ans1",
            "hint": "hint1",
        }

        with (
            patch("app.api.user_routes.get_today_answers", return_value=mock_answers),
            patch(
                "app.api.user_routes.verify_supabase_token",
                return_value=auth_principal(),
            ),
            patch(
                "app.api.user_routes.mission_session_service.create_session",
                return_value=mock_session,
            ),
        ):
            response = client.post(
                "/api/mission/start",
                json={"mission_type": "location"},
                headers=AUTH_HEADERS,
            )
            data = response.get_json()

            assert response.status_code == 200
            assert data["mission_id"] == "demo-mission"
            assert data["location_validation"]["allowed"] is True
            assert data["location_validation"]["reason"] == "gps_validation_skipped"

    def test_mission_start_rejects_missing_gps(self, client, monkeypatch):
        monkeypatch.setattr("app.api.user_routes.settings.DEMO_AUTH_ENABLED", False)
        monkeypatch.setattr("app.api.user_routes.settings.SKIP_GPS_VALIDATION", False)
        mock_answers = ("ans1", "ans2", "hint1", "hint2", "vqa1", "vqa2")

        with (
            patch("app.api.user_routes.get_today_answers", return_value=mock_answers),
            patch(
                "app.api.user_routes.verify_supabase_token",
                return_value=auth_principal(),
            ),
        ):
            payload = {"mission_type": "location", "user_id": "test_user"}
            response = client.post(
                "/api/mission/start", json=payload, headers=AUTH_HEADERS
            )
            data = response.get_json()

            assert response.status_code == 400
            assert data["error"] == "gps_required"
            assert data["location_validation"]["allowed"] is False


class TestMissionSubmitRoute:
    """POST /api/mission/submit 쿠폰 자동 발급 검증."""

    def test_successful_submission_issues_coupon_without_button_click(self, client):
        mock_session = {
            "mission_id": "mission-1",
            "mission_type": "location",
            "user_id": "guest",
            "site_id": "default",
            "answer": "지혜의숲",
            "hint": "hint",
        }
        mock_coupon = {
            "code": "AUTO1234",
            "mission_id": "mission-1",
            "user_id": "guest",
            "status": "issued",
        }
        pipeline_output = {
            "request_context": {"image_hash": "hash-1"},
            "final_response": {
                "data": {
                    "success": True,
                    "couponEligible": True,
                    "score": 0.91,
                }
            },
        }

        with (
            patch(
                "app.api.user_routes.verify_supabase_token",
                return_value=auth_principal(),
            ),
            patch(
                "app.api.user_routes.mission_session_service.can_submit",
                return_value=(True, "ok"),
            ),
            patch(
                "app.api.user_routes.mission_session_service.get_session",
                return_value=mock_session,
            ),
            patch("app.api.user_routes._validate_upload", return_value=(True, ".jpg")),
            patch(
                "app.api.user_routes.pipeline_app.invoke", return_value=pipeline_output
            ),
            patch("app.api.user_routes.mission_session_service.record_submission"),
            patch(
                "app.api.user_routes.coupon_service.issue_coupon",
                return_value=mock_coupon,
            ) as issue_coupon,
            patch(
                "app.api.user_routes.mission_session_service.mark_coupon_issued"
            ) as mark_coupon_issued,
        ):
            response = client.post(
                "/api/mission/submit",
                data={
                    "mission_id": "mission-1",
                    "client_lat": "37.711988",
                    "client_lng": "126.6867095",
                    "accuracy_meters": "20",
                    "image": (io.BytesIO(b"fake-image"), "mission.jpg"),
                },
                content_type="multipart/form-data",
                headers=AUTH_HEADERS,
            )

        data = response.get_json()

        assert response.status_code == 200
        assert data["success"] is True
        assert data["coupon"] == mock_coupon
        issue_coupon.assert_called_once_with(
            mission_type="mission1",
            answer="지혜의숲",
            mission_id="mission-1",
            user_id="guest",
        )
        mark_coupon_issued.assert_called_once_with("mission-1", "AUTO1234")

    def test_submission_rejects_outside_gps_before_pipeline(self, client, monkeypatch):
        monkeypatch.setattr("app.api.user_routes.settings.DEMO_AUTH_ENABLED", False)
        monkeypatch.setattr("app.api.user_routes.settings.SKIP_GPS_VALIDATION", False)
        mock_session = {
            "mission_id": "mission-1",
            "mission_type": "location",
            "user_id": "guest",
            "site_id": "default",
            "answer": "ans1",
            "hint": "hint",
        }

        with (
            patch(
                "app.api.user_routes.verify_supabase_token",
                return_value=auth_principal(),
            ),
            patch(
                "app.api.user_routes.mission_session_service.can_submit",
                return_value=(True, "ok"),
            ),
            patch(
                "app.api.user_routes.mission_session_service.get_session",
                return_value=mock_session,
            ),
            patch("app.api.user_routes.pipeline_app.invoke") as invoke,
        ):
            response = client.post(
                "/api/mission/submit",
                data={
                    "mission_id": "mission-1",
                    "client_lat": "37.720000",
                    "client_lng": "126.700000",
                    "accuracy_meters": "20",
                    "image": (io.BytesIO(b"fake-image"), "mission.jpg"),
                },
                content_type="multipart/form-data",
                headers=AUTH_HEADERS,
            )
            data = response.get_json()

        assert response.status_code == 400
        assert data["error"] == "outside_mission_site"
        invoke.assert_not_called()


class TestCouponRedeemRoute:
    """POST /api/coupon/redeem 엔드포인트 검증."""

    def test_redeem_success(self, client):
        """쿠폰 사용 성공 시 200을 반환한다."""
        mock_result = {"redeem_status": "redeemed", "message": "Success"}
        with patch(
            "app.api.user_routes.coupon_service.redeem_coupon", return_value=mock_result
        ):
            payload = {"coupon_code": "ABC-123", "partner_pos_id": "POS-01"}
            response = client.post("/api/coupon/redeem", json=payload)

            assert response.status_code == 200
            assert response.get_json()["redeem_status"] == "redeemed"

    def test_redeem_fail_already_used(self, client):
        """이미 사용된 쿠폰은 400(또는 로직에 따른 코드)을 반환한다."""
        mock_result = {"redeem_status": "already_redeemed", "message": "Already used"}
        with patch(
            "app.api.user_routes.coupon_service.redeem_coupon", return_value=mock_result
        ):
            payload = {"coupon_code": "USED-01", "partner_pos_id": "POS-01"}
            response = client.post("/api/coupon/redeem", json=payload)

            assert response.status_code == 400
            assert response.get_json()["redeem_status"] == "already_redeemed"
