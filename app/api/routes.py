"""REST API routes for mission workflow and coupon lifecycle."""

from __future__ import annotations

import io
import os
import tempfile

from flask import Blueprint, jsonify, request, send_file
from PIL import Image
from pillow_heif import register_heif_opener

from app.core.config import settings
from app.council.graph import pipeline_app
from app.services.answer_service import get_today_answers
from app.services.coupon_service import coupon_service
from app.services.mission_session_service import mission_session_service

api = Blueprint("api", __name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def _normalize_mission_type(mission_type: str) -> str:
    """Caller: ?? ?? ???? ???
    Purpose: `_normalize_mission_type` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: mission_type: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    if mission_type == "photo":
        return "atmosphere"
    return mission_type if mission_type in {"location", "atmosphere"} else "location"


def _legacy_mission_type(mission_type: str) -> str:
    """Caller: ?? ?? ???? ???
    Purpose: `_legacy_mission_type` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: mission_type: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    return "photo" if mission_type == "atmosphere" else mission_type


def _validate_upload(file_obj):
    """Caller: ?? ?? ???? ???
    Purpose: `_validate_upload` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: file_obj: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    if not file_obj:
        return False, "이미지 파일이 없습니다."
    if file_obj.filename == "":
        return False, "파일이 선택되지 않았습니다."
    ext = os.path.splitext(file_obj.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, "지원하지 않는 파일 형식입니다."
    return True, ext


@api.route("/get-today-hint", methods=["GET"])
def get_today_hint():
    """Caller: ?? ?? ???? ???
    Purpose: `get_today_hint` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: None
    Note: ?? ?? ?? ???? ???"""
    mission_type = _normalize_mission_type(request.args.get("mission_type", "location"))
    try:
        a1, a2, h1, h2 = get_today_answers()
        if mission_type == "atmosphere":
            return jsonify({"answer": a2, "hint": h2})
        return jsonify({"answer": a1, "hint": h1})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api.route("/api/preview", methods=["POST"])
def api_preview():
    """Caller: ?? ?? ???? ???
    Purpose: `api_preview` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: None
    Note: ?? ?? ?? ???? ???"""
    file_obj = request.files.get("image")
    valid, ext_or_msg = _validate_upload(file_obj)
    if not valid:
        return jsonify({"error": ext_or_msg}), 400

    register_heif_opener()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext_or_msg) as temp_file:
        file_obj.save(temp_file.name)
        temp_path = temp_file.name

    try:
        image = Image.open(temp_path).convert("RGB")
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=90)
        output.seek(0)
        return send_file(output, mimetype="image/jpeg", download_name="preview.jpg")
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@api.route("/api/mission/start", methods=["POST"])
def mission_start():
    """Caller: ?? ?? ???? ???
    Purpose: `mission_start` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: None
    Note: ?? ?? ?? ???? ???"""
    payload = request.get_json(silent=True) or {}
    mission_type = _normalize_mission_type(payload.get("mission_type", "location"))
    user_id = payload.get("user_id", "guest")
    site_id = payload.get("site_id", "pazule-default")

    a1, a2, h1, h2 = get_today_answers()
    if mission_type == "atmosphere":
        answer, hint = a2, h2
    else:
        answer, hint = a1, h1

    session = mission_session_service.create_session(
        user_id=user_id,
        site_id=site_id,
        mission_type=mission_type,
        answer=answer,
        hint=hint,
    )

    return jsonify(
        {
            "mission_id": session["mission_id"],
            "mission_type": _legacy_mission_type(session["mission_type"]),
            "eligibility": {"allowed": True},
            "constraints": {
                "max_submissions": session["max_submissions"],
                "expires_at": session["expires_at"],
                "site_radius_meters": settings.MISSION_SITE_RADIUS_METERS,
            },
            "hint": hint,
        }
    )


@api.route("/api/mission/submit", methods=["POST"])
def mission_submit():
    """Caller: ?? ?? ???? ???
    Purpose: `mission_submit` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: None
    Note: ?? ?? ?? ???? ???"""
    mission_id = request.form.get("mission_id")
    if not mission_id:
        return jsonify({"error": "mission_id is required"}), 400

    can_submit, reason = mission_session_service.can_submit(mission_id)
    if not can_submit:
        return jsonify({"error": reason}), 400

    session = mission_session_service.get_session(mission_id)
    if not session:
        return jsonify({"error": "session_not_found"}), 404

    file_obj = request.files.get("image")
    valid, ext_or_msg = _validate_upload(file_obj)
    if not valid:
        return jsonify({"error": ext_or_msg}), 400

    model_selection = request.form.get("model_selection")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext_or_msg) as temp_file:
        file_obj.save(temp_file.name)
        temp_path = temp_file.name

    try:
        initial_state = {
            "request_context": {
                "mission_id": mission_id,
                "user_id": session.get("user_id", "guest"),
                "site_id": session.get("site_id", "pazule-default"),
                "mission_type": session.get("mission_type", "location"),
                "image_path": temp_path,
                "answer": session.get("answer"),
                "model_selection": model_selection,
            },
            "artifacts": {},
            "errors": [],
            "control_flags": {},
            "messages": [],
        }
        output = pipeline_app.invoke(initial_state)
        final_res = output.get("final_response", {})
        final_data = final_res.get("data", {"success": False, "error": "pipeline_failed"})

        image_hash = output.get("request_context", {}).get("image_hash")
        if image_hash:
            mission_session_service.record_submission(mission_id, image_hash, final_data)

        final_data["mission_id"] = mission_id
        return jsonify(final_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@api.route("/api/coupon/issue", methods=["POST"])
def coupon_issue():
    """Caller: ?? ?? ???? ???
    Purpose: `coupon_issue` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: None
    Note: ?? ?? ?? ???? ???"""
    payload = request.get_json(silent=True) or {}
    mission_id = payload.get("mission_id")
    partner_id = payload.get("partner_id")
    if not mission_id:
        return jsonify({"error": "mission_id is required"}), 400

    session = mission_session_service.get_session(mission_id)
    if not session:
        return jsonify({"error": "session_not_found"}), 404

    latest = session.get("latest_judgment") or {}
    if not latest.get("success"):
        return jsonify({"error": "mission_not_successful"}), 400
    if not latest.get("couponEligible", True):
        return jsonify({"error": "coupon_not_eligible"}), 400

    mission_type = session.get("mission_type", "location")
    coupon = coupon_service.issue_coupon(
        mission_type="mission1" if mission_type == "location" else "mission2",
        answer=session.get("answer", ""),
        mission_id=mission_id,
        partner_id=partner_id,
    )
    mission_session_service.mark_coupon_issued(mission_id, coupon["code"])
    return jsonify(coupon)


@api.route("/api/coupon/redeem", methods=["POST"])
def coupon_redeem():
    """Caller: ?? ?? ???? ???
    Purpose: `coupon_redeem` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: None
    Note: ?? ?? ?? ???? ???"""
    payload = request.get_json(silent=True) or {}
    coupon_code = payload.get("coupon_code")
    partner_pos_id = payload.get("partner_pos_id")
    if not coupon_code or not partner_pos_id:
        return jsonify({"error": "coupon_code and partner_pos_id are required"}), 400
    result = coupon_service.redeem_coupon(coupon_code, partner_pos_id)
    status = 200 if result.get("redeem_status") == "redeemed" else 400
    return jsonify(result), status
