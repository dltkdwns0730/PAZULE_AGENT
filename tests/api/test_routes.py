"""REST API routes 단위 테스트.

공공 환경 호환 설계:
  - 실제 AI 모델 로딩 없음 — pipeline_app.invoke() mock
  - 실제 파일 I/O 없음 — mission_session_service / coupon_service mock
  - 실제 이미지 처리 없음 — PIL.Image mock
  - Flask test client 사용 (실제 HTTP 스택 통과)

검증 대상:
  - _validate_upload: 파일 없음 / 파일명 없음 / 잘못된 확장자 / 정상
  - GET /get-today-hint: location / atmosphere / photo 정규화 / 예외 → 500
  - POST /api/preview: 400 (검증 실패) / 200 (정상 변환) / 500 (PIL 예외)
  - POST /api/mission/start: 정상 / atmosphere / 기본값
  - POST /api/mission/submit: mission_id 없음 / can_submit 실패 / 세션 없음
                              파일 없음 / 정상 / 파이프라인 예외
  - POST /api/coupon/issue: mission_id 없음 / 세션 없음 / 미션 실패 / 정상
  - POST /api/coupon/redeem: 필드 누락 / 성공 / 실패
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def app():
    """최소 Flask 앱에 api Blueprint만 등록 (heavy dependency 없이)."""
    from app.api.routes import api

    flask_app = Flask(__name__)
    flask_app.register_blueprint(api)
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def _fake_image_bytes() -> bytes:
    """PIL 없이 fake JPEG bytes 반환."""
    return b"\xff\xd8\xff\xe0" + b"\x00" * 100


def _make_file_storage(filename: str = "test.jpg", content: bytes = b"fake image"):
    """werkzeug FileStorage 오브젝트 모킹."""
    from werkzeug.datastructures import FileStorage

    return FileStorage(
        stream=io.BytesIO(content),
        filename=filename,
        content_type="image/jpeg",
    )


# ── _validate_upload ──────────────────────────────────────────────────────────


class TestValidateUpload:
    """_validate_upload() 직접 호출 단위 테스트 (Flask 컨텍스트 불필요)."""

    def _validate(self, file_obj):
        from app.api.routes import _validate_upload

        return _validate_upload(file_obj)

    def test_none_file_returns_false(self) -> None:
        ok, msg = self._validate(None)
        print(f"\n[_validate_upload] None → ok={ok}, msg={msg}")
        assert ok is False
        assert "없습니다" in msg

    def test_empty_filename_returns_false(self) -> None:
        mock_file = MagicMock()
        mock_file.filename = ""
        ok, msg = self._validate(mock_file)
        assert ok is False
        assert "선택" in msg

    def test_invalid_extension_returns_false(self) -> None:
        mock_file = MagicMock()
        mock_file.filename = "script.py"
        ok, msg = self._validate(mock_file)
        assert ok is False
        assert "지원" in msg

    def test_jpg_extension_valid(self) -> None:
        mock_file = MagicMock()
        mock_file.filename = "photo.jpg"
        ok, ext = self._validate(mock_file)
        assert ok is True
        assert ext == ".jpg"

    def test_jpeg_extension_valid(self) -> None:
        mock_file = MagicMock()
        mock_file.filename = "photo.JPEG"
        ok, ext = self._validate(mock_file)
        assert ok is True
        assert ext == ".jpeg"

    def test_png_extension_valid(self) -> None:
        mock_file = MagicMock()
        mock_file.filename = "photo.PNG"
        ok, ext = self._validate(mock_file)
        assert ok is True
        assert ext == ".png"

    def test_heic_extension_valid(self) -> None:
        mock_file = MagicMock()
        mock_file.filename = "photo.heic"
        ok, ext = self._validate(mock_file)
        assert ok is True
        assert ext == ".heic"

    def test_heif_extension_valid(self) -> None:
        mock_file = MagicMock()
        mock_file.filename = "photo.heif"
        ok, ext = self._validate(mock_file)
        assert ok is True
        assert ext == ".heif"

    def test_gif_extension_invalid(self) -> None:
        mock_file = MagicMock()
        mock_file.filename = "anim.gif"
        ok, msg = self._validate(mock_file)
        assert ok is False


# ── GET /get-today-hint ───────────────────────────────────────────────────────


class TestGetTodayHint:
    def _run(
        self, client, mission_type: str | None = None, answers=("a1", "a2", "h1", "h2")
    ):
        with patch("app.api.routes.get_today_answers", return_value=answers):
            url = "/get-today-hint"
            if mission_type:
                url += f"?mission_type={mission_type}"
            return client.get(url)

    def test_location_returns_answer1(self, client) -> None:
        resp = self._run(
            client, "location", ("loc_answer", "atm_answer", "loc_hint", "atm_hint")
        )
        print(f"\n[GET /get-today-hint] location → {resp.get_json()}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["answer"] == "loc_answer"
        assert data["hint"] == "loc_hint"

    def test_atmosphere_returns_answer2(self, client) -> None:
        resp = self._run(
            client, "atmosphere", ("loc_answer", "atm_answer", "loc_hint", "atm_hint")
        )
        data = resp.get_json()
        assert data["answer"] == "atm_answer"
        assert data["hint"] == "atm_hint"

    def test_photo_normalized_to_atmosphere(self, client) -> None:
        """'photo' → 'atmosphere' 정규화 검증."""
        resp = self._run(
            client, "photo", ("loc_answer", "atm_answer", "loc_hint", "atm_hint")
        )
        data = resp.get_json()
        assert data["answer"] == "atm_answer"

    def test_default_no_param_returns_location(self, client) -> None:
        resp = self._run(
            client, None, ("loc_answer", "atm_answer", "loc_hint", "atm_hint")
        )
        data = resp.get_json()
        assert data["answer"] == "loc_answer"

    def test_exception_returns_500(self, client) -> None:
        with patch(
            "app.api.routes.get_today_answers", side_effect=RuntimeError("disk error")
        ):
            resp = client.get("/get-today-hint")
        assert resp.status_code == 500
        assert "error" in resp.get_json()

    def test_response_has_answer_and_hint_keys(self, client) -> None:
        resp = self._run(client, "location")
        data = resp.get_json()
        assert "answer" in data
        assert "hint" in data


# ── POST /api/preview ─────────────────────────────────────────────────────────


class TestApiPreview:
    def _post_image(self, client, filename: str = "test.jpg", content: bytes = b"img"):
        data = {"image": (io.BytesIO(content), filename)}
        return client.post(
            "/api/preview", data=data, content_type="multipart/form-data"
        )

    def test_no_file_returns_400(self, client) -> None:
        resp = client.post("/api/preview", data={}, content_type="multipart/form-data")
        print(f"\n[POST /api/preview] no file → {resp.status_code}")
        assert resp.status_code == 400

    def test_invalid_extension_returns_400(self, client) -> None:
        resp = self._post_image(client, filename="script.exe")
        assert resp.status_code == 400

    def test_valid_image_returns_jpeg(self, client) -> None:
        """PIL.Image.open mock → 200 + image/jpeg 반환."""
        mock_image = MagicMock()
        mock_image.convert.return_value = mock_image
        mock_image.save = lambda buf, **kw: buf.write(_fake_image_bytes())

        with (
            patch("app.api.routes.register_heif_opener"),
            patch("app.api.routes.Image.open", return_value=mock_image),
        ):
            resp = self._post_image(client, "photo.jpg")
        print(f"\n[POST /api/preview] valid → {resp.status_code} {resp.content_type}")
        assert resp.status_code == 200
        assert "image" in resp.content_type

    def test_pil_exception_returns_500(self, client) -> None:
        with (
            patch("app.api.routes.register_heif_opener"),
            patch("app.api.routes.Image.open", side_effect=OSError("corrupt file")),
        ):
            resp = self._post_image(client, "photo.jpg")
        assert resp.status_code == 500
        assert "error" in resp.get_json()

    def test_empty_filename_returns_400(self, client) -> None:
        """빈 filename → _validate_upload 실패 → 400."""
        data = {"image": (io.BytesIO(b"data"), "")}
        resp = client.post(
            "/api/preview", data=data, content_type="multipart/form-data"
        )
        assert resp.status_code == 400


# ── POST /api/mission/start ───────────────────────────────────────────────────


class TestMissionStart:
    _FAKE_SESSION = {
        "mission_id": "test-mission-id",
        "mission_type": "location",
        "max_submissions": 3,
        "expires_at": "2099-01-01T00:00:00+00:00",
    }

    def _run(
        self,
        client,
        payload: dict | None = None,
        answers=("loc_ans", "atm_ans", "loc_hint", "atm_hint"),
        session: dict | None = None,
    ):
        if session is None:
            session = self._FAKE_SESSION.copy()
        with (
            patch("app.api.routes.get_today_answers", return_value=answers),
            patch("app.api.routes.mission_session_service") as mock_svc,
            patch("app.api.routes.settings") as mock_settings,
        ):
            mock_svc.create_session.return_value = session
            mock_settings.MISSION_SITE_RADIUS_METERS = 100
            resp = client.post(
                "/api/mission/start",
                json=payload or {"mission_type": "location", "user_id": "u1"},
            )
        return resp

    def test_returns_200(self, client) -> None:
        resp = self._run(client)
        print(f"\n[POST /api/mission/start] → {resp.get_json()}")
        assert resp.status_code == 200

    def test_response_has_mission_id(self, client) -> None:
        resp = self._run(client)
        assert "mission_id" in resp.get_json()

    def test_response_has_constraints(self, client) -> None:
        resp = self._run(client)
        data = resp.get_json()
        assert "constraints" in data
        assert "max_submissions" in data["constraints"]
        assert "expires_at" in data["constraints"]

    def test_response_has_hint(self, client) -> None:
        resp = self._run(client)
        data = resp.get_json()
        assert "hint" in data
        assert data["hint"] == "loc_hint"

    def test_atmosphere_uses_answer2(self, client) -> None:
        session = {**self._FAKE_SESSION, "mission_type": "atmosphere"}
        resp = self._run(
            client,
            payload={"mission_type": "atmosphere"},
            answers=("loc_ans", "atm_ans", "loc_hint", "atm_hint"),
            session=session,
        )
        data = resp.get_json()
        assert data["hint"] == "atm_hint"

    def test_default_user_id_is_guest(self, client) -> None:
        """user_id 없이 요청 시 create_session에 'guest' 전달."""
        with (
            patch(
                "app.api.routes.get_today_answers", return_value=("a", "b", "h", "h2")
            ),
            patch("app.api.routes.mission_session_service") as mock_svc,
            patch("app.api.routes.settings") as mock_settings,
        ):
            mock_svc.create_session.return_value = self._FAKE_SESSION.copy()
            mock_settings.MISSION_SITE_RADIUS_METERS = 100
            client.post("/api/mission/start", json={})
        call_kwargs = mock_svc.create_session.call_args[1]
        assert call_kwargs.get("user_id") == "guest"

    def test_eligibility_always_allowed(self, client) -> None:
        resp = self._run(client)
        data = resp.get_json()
        assert data["eligibility"]["allowed"] is True

    def test_mission_type_legacy_conversion(self, client) -> None:
        """atmosphere → 'photo' 레거시 변환."""
        session = {**self._FAKE_SESSION, "mission_type": "atmosphere"}
        resp = self._run(
            client,
            payload={"mission_type": "atmosphere"},
            session=session,
        )
        assert resp.get_json()["mission_type"] == "photo"


# ── POST /api/mission/submit ──────────────────────────────────────────────────


class TestMissionSubmit:
    _FAKE_SESSION = {
        "mission_id": "m1",
        "user_id": "u1",
        "site_id": "s1",
        "mission_type": "location",
        "answer": "target_answer",
    }
    _FAKE_PIPELINE = {
        "final_response": {"data": {"success": True, "confidence": 0.9}},
        "request_context": {"image_hash": "abc123"},
    }

    _SENTINEL = object()  # "use default" sentinel — distinguishes from explicit None

    def _post_submit(
        self,
        client,
        mission_id: str = "m1",
        filename: str = "test.jpg",
        can_submit: tuple = (True, "ok"),
        session=_SENTINEL,
        pipeline_output: dict | None = None,
        pipeline_exc: Exception | None = None,
    ):
        # None is a valid explicit value (session not found); use sentinel for default
        resolved_session = (
            self._FAKE_SESSION.copy() if session is self._SENTINEL else session
        )
        if pipeline_output is None:
            pipeline_output = self._FAKE_PIPELINE.copy()

        data = {}
        if mission_id:
            data["mission_id"] = mission_id
        if filename:
            data["image"] = (io.BytesIO(b"fake img"), filename)

        with (
            patch("app.api.routes.mission_session_service") as mock_svc,
            patch("app.api.routes.pipeline_app") as mock_pipeline,
        ):
            mock_svc.can_submit.return_value = can_submit
            mock_svc.get_session.return_value = resolved_session
            mock_svc.record_submission.return_value = resolved_session or {}
            if pipeline_exc:
                mock_pipeline.invoke.side_effect = pipeline_exc
            else:
                mock_pipeline.invoke.return_value = pipeline_output
            resp = client.post(
                "/api/mission/submit",
                data=data,
                content_type="multipart/form-data",
            )
        return resp

    def test_no_mission_id_returns_400(self, client) -> None:
        resp = self._post_submit(client, mission_id="")
        print(f"\n[POST /api/mission/submit] no mission_id → {resp.status_code}")
        assert resp.status_code == 400
        assert "mission_id" in resp.get_json()["error"]

    def test_cannot_submit_returns_400(self, client) -> None:
        resp = self._post_submit(client, can_submit=(False, "session_expired"))
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "session_expired"

    def test_session_not_found_returns_404(self, client) -> None:
        resp = self._post_submit(client, session=None, can_submit=(True, "ok"))
        assert resp.status_code == 404

    def test_no_file_returns_400(self, client) -> None:
        resp = self._post_submit(client, filename="")
        assert resp.status_code == 400

    def test_invalid_file_extension_returns_400(self, client) -> None:
        resp = self._post_submit(client, filename="virus.exe")
        assert resp.status_code == 400

    def test_valid_submit_returns_200(self, client) -> None:
        resp = self._post_submit(client)
        print(
            f"\n[POST /api/mission/submit] valid → {resp.status_code} {resp.get_json()}"
        )
        assert resp.status_code == 200

    def test_valid_submit_has_mission_id(self, client) -> None:
        resp = self._post_submit(client)
        data = resp.get_json()
        assert "mission_id" in data
        assert data["mission_id"] == "m1"

    def test_valid_submit_has_success_field(self, client) -> None:
        resp = self._post_submit(client)
        assert "success" in resp.get_json()

    def test_pipeline_exception_returns_500(self, client) -> None:
        resp = self._post_submit(client, pipeline_exc=RuntimeError("GPU error"))
        assert resp.status_code == 500
        assert "error" in resp.get_json()

    def test_pipeline_called_with_correct_mission_type(self, client) -> None:
        """pipeline_app.invoke에 session의 mission_type이 전달되는지 검증."""
        with (
            patch("app.api.routes.mission_session_service") as mock_svc,
            patch("app.api.routes.pipeline_app") as mock_pipeline,
        ):
            mock_svc.can_submit.return_value = (True, "ok")
            mock_svc.get_session.return_value = self._FAKE_SESSION.copy()
            mock_svc.record_submission.return_value = self._FAKE_SESSION.copy()
            mock_pipeline.invoke.return_value = self._FAKE_PIPELINE.copy()
            client.post(
                "/api/mission/submit",
                data={"mission_id": "m1", "image": (io.BytesIO(b"img"), "test.jpg")},
                content_type="multipart/form-data",
            )
        call_state = mock_pipeline.invoke.call_args[0][0]
        assert call_state["request_context"]["mission_type"] == "location"

    def test_submission_limit_reason_in_error(self, client) -> None:
        """제출 한도 초과 시 reason이 응답에 포함됨."""
        resp = self._post_submit(client, can_submit=(False, "submission_limit_reached"))
        data = resp.get_json()
        assert data["error"] == "submission_limit_reached"


# ── POST /api/coupon/issue ────────────────────────────────────────────────────


class TestCouponIssue:
    _FAKE_SESSION_SUCCESS = {
        "mission_id": "m1",
        "mission_type": "location",
        "answer": "gangnam_station",
        "latest_judgment": {"success": True, "couponEligible": True},
    }
    _FAKE_COUPON = {
        "code": "ABCD1234",
        "discount_rule": "10%_OFF",
        "mission_type": "mission1",
    }

    def _run(
        self,
        client,
        payload: dict | None = None,
        session: dict | None = None,
        coupon: dict | None = None,
    ):
        if coupon is None:
            coupon = self._FAKE_COUPON.copy()
        with (
            patch("app.api.routes.mission_session_service") as mock_svc,
            patch("app.api.routes.coupon_service") as mock_coupon,
        ):
            mock_svc.get_session.return_value = session
            mock_svc.mark_coupon_issued.return_value = session or {}
            mock_coupon.issue_coupon.return_value = coupon
            resp = client.post(
                "/api/coupon/issue",
                json=payload if payload is not None else {"mission_id": "m1"},
            )
        return resp

    def test_no_mission_id_returns_400(self, client) -> None:
        resp = self._run(client, payload={})
        print(f"\n[POST /api/coupon/issue] no mission_id → {resp.status_code}")
        assert resp.status_code == 400

    def test_session_not_found_returns_404(self, client) -> None:
        resp = self._run(client, session=None)
        assert resp.status_code == 404

    def test_mission_not_successful_returns_400(self, client) -> None:
        session = {**self._FAKE_SESSION_SUCCESS, "latest_judgment": {"success": False}}
        resp = self._run(client, session=session)
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "mission_not_successful"

    def test_coupon_not_eligible_returns_400(self, client) -> None:
        session = {
            **self._FAKE_SESSION_SUCCESS,
            "latest_judgment": {"success": True, "couponEligible": False},
        }
        resp = self._run(client, session=session)
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "coupon_not_eligible"

    def test_valid_issue_returns_200(self, client) -> None:
        resp = self._run(client, session=self._FAKE_SESSION_SUCCESS.copy())
        print(
            f"\n[POST /api/coupon/issue] valid → {resp.status_code} {resp.get_json()}"
        )
        assert resp.status_code == 200

    def test_valid_issue_returns_coupon_code(self, client) -> None:
        resp = self._run(client, session=self._FAKE_SESSION_SUCCESS.copy())
        data = resp.get_json()
        assert data["code"] == "ABCD1234"

    def test_atmosphere_mission_uses_mission2_type(self, client) -> None:
        """atmosphere 미션 → coupon_service.issue_coupon에 'mission2' 전달."""
        session = {
            **self._FAKE_SESSION_SUCCESS,
            "mission_type": "atmosphere",
        }
        with (
            patch("app.api.routes.mission_session_service") as mock_svc,
            patch("app.api.routes.coupon_service") as mock_coupon,
        ):
            mock_svc.get_session.return_value = session
            mock_svc.mark_coupon_issued.return_value = {}
            mock_coupon.issue_coupon.return_value = self._FAKE_COUPON.copy()
            client.post("/api/coupon/issue", json={"mission_id": "m1"})
        call_kwargs = mock_coupon.issue_coupon.call_args[1]
        assert call_kwargs["mission_type"] == "mission2"

    def test_location_mission_uses_mission1_type(self, client) -> None:
        """location 미션 → coupon_service.issue_coupon에 'mission1' 전달."""
        with (
            patch("app.api.routes.mission_session_service") as mock_svc,
            patch("app.api.routes.coupon_service") as mock_coupon,
        ):
            mock_svc.get_session.return_value = self._FAKE_SESSION_SUCCESS.copy()
            mock_svc.mark_coupon_issued.return_value = {}
            mock_coupon.issue_coupon.return_value = self._FAKE_COUPON.copy()
            client.post("/api/coupon/issue", json={"mission_id": "m1"})
        call_kwargs = mock_coupon.issue_coupon.call_args[1]
        assert call_kwargs["mission_type"] == "mission1"


# ── POST /api/coupon/redeem ───────────────────────────────────────────────────


class TestCouponRedeem:
    def _run(self, client, payload: dict, redeem_result: dict | None = None):
        if redeem_result is None:
            redeem_result = {"redeem_status": "redeemed", "message": "success"}
        with patch("app.api.routes.coupon_service") as mock_coupon:
            mock_coupon.redeem_coupon.return_value = redeem_result
            resp = client.post("/api/coupon/redeem", json=payload)
        return resp

    def test_missing_coupon_code_returns_400(self, client) -> None:
        resp = self._run(client, {"partner_pos_id": "pos1"})
        print(f"\n[POST /api/coupon/redeem] no coupon_code → {resp.status_code}")
        assert resp.status_code == 400

    def test_missing_partner_pos_id_returns_400(self, client) -> None:
        resp = self._run(client, {"coupon_code": "ABCD1234"})
        assert resp.status_code == 400

    def test_both_missing_returns_400(self, client) -> None:
        resp = self._run(client, {})
        assert resp.status_code == 400

    def test_error_message_on_missing_fields(self, client) -> None:
        resp = self._run(client, {})
        data = resp.get_json()
        assert "error" in data

    def test_successful_redeem_returns_200(self, client) -> None:
        resp = self._run(
            client,
            {"coupon_code": "ABCD1234", "partner_pos_id": "pos1"},
            {"redeem_status": "redeemed", "message": "ok"},
        )
        print(
            f"\n[POST /api/coupon/redeem] success → {resp.status_code} {resp.get_json()}"
        )
        assert resp.status_code == 200

    def test_failed_redeem_returns_400(self, client) -> None:
        resp = self._run(
            client,
            {"coupon_code": "BADCODE", "partner_pos_id": "pos1"},
            {"redeem_status": "already_redeemed", "message": "used"},
        )
        assert resp.status_code == 400

    def test_redeem_result_in_response_body(self, client) -> None:
        result = {"redeem_status": "redeemed", "message": "ok", "coupon": {"code": "X"}}
        resp = self._run(
            client,
            {"coupon_code": "ABCD1234", "partner_pos_id": "pos1"},
            result,
        )
        data = resp.get_json()
        assert data["redeem_status"] == "redeemed"

    def test_coupon_service_called_with_code_and_pos(self, client) -> None:
        """coupon_service.redeem_coupon에 올바른 인수 전달 검증."""
        with patch("app.api.routes.coupon_service") as mock_coupon:
            mock_coupon.redeem_coupon.return_value = {"redeem_status": "redeemed"}
            client.post(
                "/api/coupon/redeem",
                json={"coupon_code": "XYZ", "partner_pos_id": "POS99"},
            )
        mock_coupon.redeem_coupon.assert_called_once_with("XYZ", "POS99")
