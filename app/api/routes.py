"""REST API routes for mission workflow and coupon lifecycle."""

from __future__ import annotations

import io
import logging
import os
import tempfile

from flask import Blueprint, Response, jsonify, request, send_file
from PIL import Image
from pillow_heif import register_heif_opener

from app.core.config import constants, settings
from app.core.utils import normalize_mission_type, to_legacy_mission_type
from app.council.graph import pipeline_app
from app.services.answer_service import get_today_answers
from app.services.coupon_service import coupon_service
from app.services.mission_session_service import mission_session_service

logger = logging.getLogger(__name__)

api = Blueprint("api", __name__)


# Local helper functions _normalize_mission_type and _legacy_mission_type removed
# and replaced by app.core.utils functions for consolidation.


def _validate_upload(file_obj) -> tuple[bool, str]:
    """업로드 파일의 존재·파일명·확장자를 검증한다.

    Args:
        file_obj: Flask request.files 객체.

    Returns:
        성공 시 (True, ext), 실패 시 (False, error_message).
    """
    if not file_obj:
        return False, "이미지 파일이 없습니다."
    if file_obj.filename == "":
        return False, "파일이 선택되지 않았습니다."
    ext = os.path.splitext(file_obj.filename)[1].lower()
    if ext not in constants.ALLOWED_UPLOAD_EXTENSIONS:
        return False, "지원하지 않는 파일 형식입니다."
    return True, ext


@api.route("/get-today-hint", methods=["GET"])
def get_today_hint() -> Response:
    """오늘의 미션 정답 힌트를 반환한다.

    Query Params:
        mission_type: 'location' | 'atmosphere' | 'photo' (기본값: 'location').
        user_id: 사용자 식별자 (기본값: 'guest').

    Returns:
        JSON {"answer": str, "hint": str, "completed": bool} 또는 {"error": str} (500).
    """
    mission_type = normalize_mission_type(request.args.get("mission_type", "location"))
    user_id = request.args.get("user_id", "guest")
    try:
        a1, a2, h1, h2, vqa1, vqa2 = get_today_answers()

        # 1. 오늘 미션 성공 여부 확인
        completed_by_session = mission_session_service.is_mission_completed_today(
            user_id, mission_type
        )

        # 2. 해당 정답에 대한 쿠폰 보유 여부 확인 (최종 보상 획득 여부)
        answer = a2 if mission_type == "atmosphere" else a1
        completed_by_coupon = coupon_service.has_coupon_for_answer(user_id, answer)

        # 둘 중 하나라도 참이면 완료로 간주
        completed = completed_by_session or completed_by_coupon

        if mission_type == "atmosphere":
            return jsonify(
                {"answer": a2, "hint": h2, "vqa_hints": vqa2, "completed": completed}
            )
        return jsonify(
            {"answer": a1, "hint": h1, "vqa_hints": vqa1, "completed": completed}
        )

    except Exception as exc:
        logger.exception("get_today_hint 처리 중 오류 발생")
        return jsonify({"error": str(exc)}), 500


@api.route("/api/preview", methods=["POST"])
def api_preview() -> Response:
    """업로드 이미지를 JPEG로 변환해 미리보기 스트림을 반환한다.

    Form Data:
        image: 이미지 파일 (jpg/png/heic/heif).

    Returns:
        JPEG 이미지 스트림 또는 {"error": str} (400 | 500).
    """
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
        logger.exception("api_preview 이미지 변환 실패: %s", temp_path)
        return jsonify({"error": str(exc)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@api.route("/api/mission/start", methods=["POST"])
def mission_start() -> Response:
    """미션 세션을 생성하고 미션 정보를 반환한다.

    Request JSON:
        mission_type: 'location' | 'atmosphere' | 'photo' (기본값: 'location').
        user_id: 사용자 식별자 (기본값: 'guest').
        site_id: 사이트 식별자 (기본값: 'pazule-default').

    Returns:
        JSON {mission_id, mission_type, eligibility, constraints, hint}.
    """
    payload = request.get_json(silent=True) or {}
    mission_type = normalize_mission_type(payload.get("mission_type", "location"))
    user_id = payload.get("user_id", "guest")
    site_id = payload.get("site_id", "pazule-default")

    a1, a2, h1, h2, vqa1, vqa2 = get_today_answers()

    # 미션 시작 전 당일 완료 여부 최종 검증 (보안 강화)
    if mission_session_service.is_mission_completed_today(user_id, mission_type):
        return jsonify(
            {"error": "오늘 이미 완료한 미션입니다.", "completed": True}
        ), 400

    if mission_type == "atmosphere":
        answer, hint, vqa_hints = a2, h2, vqa2
    else:
        answer, hint, vqa_hints = a1, h1, vqa1

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
            "mission_type": to_legacy_mission_type(session["mission_type"]),
            "eligibility": {"allowed": True},
            "constraints": {
                "max_submissions": session["max_submissions"],
                "expires_at": session["expires_at"],
                "site_radius_meters": settings.MISSION_SITE_RADIUS_METERS,
            },
            "hint": hint,
            "vqa_hints": vqa_hints,
        }
    )


@api.route("/api/mission/submit", methods=["POST"])
def mission_submit() -> Response:
    """미션 이미지를 제출하고 AI 판정 결과를 반환한다.

    Form Data:
        mission_id: 미션 세션 ID.
        image: 이미지 파일 (jpg/png/heic/heif).
        model_selection: (선택) 사용할 모델 식별자.

    Returns:
        JSON 판정 결과 또는 {"error": str} (400 | 404 | 500).
    """
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
                "static_hint": session.get("hint", ""),
                "model_selection": model_selection,
            },
            "artifacts": {},
            "errors": [],
            "control_flags": {},
            "messages": [],
        }
        output = pipeline_app.invoke(initial_state)
        final_res = output.get("final_response", {})
        final_data = final_res.get(
            "data", {"success": False, "error": "pipeline_failed"}
        )

        image_hash = output.get("request_context", {}).get("image_hash")
        if image_hash:
            mission_session_service.record_submission(
                mission_id, image_hash, final_data
            )

        final_data["mission_id"] = mission_id
        return jsonify(final_data)
    except Exception as exc:
        logger.exception(
            "mission_submit 파이프라인 실행 실패: mission_id=%s", mission_id
        )
        return jsonify({"error": str(exc)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@api.route("/api/coupon/issue", methods=["POST"])
def coupon_issue() -> Response:
    """미션 성공 세션에 대해 쿠폰을 발급한다 (멱등성 보장).

    Request JSON:
        mission_id: 미션 세션 ID.
        user_id: (선택) 사용자 식별자 (기본값: 세션의 user_id).
        partner_id: (선택) 파트너 식별자.

    Returns:
        JSON 쿠폰 정보 또는 {"error": str} (400 | 404).
    """
    payload = request.get_json(silent=True) or {}
    mission_id = payload.get("mission_id")
    user_id = payload.get("user_id")
    partner_id = payload.get("partner_id")

    if not mission_id:
        return jsonify({"error": "mission_id is required"}), 400

    session = mission_session_service.get_session(mission_id)
    if not session:
        return jsonify({"error": "session_not_found"}), 404

    # 요청에 user_id가 없으면 세션의 것을 사용, 그것도 없으면 'guest'
    final_user_id = user_id or session.get("user_id", "guest")

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
        user_id=final_user_id,
        partner_id=partner_id,
    )
    mission_session_service.mark_coupon_issued(mission_id, coupon["code"])
    return jsonify(coupon)


@api.route("/api/coupon/redeem", methods=["POST"])
def coupon_redeem() -> Response:
    """쿠폰을 사용 처리한다.

    Request JSON:
        coupon_code: 쿠폰 코드.
        partner_pos_id: POS 단말 식별자.

    Returns:
        JSON {redeem_status, message, coupon} — 성공 200, 실패 400.
    """
    payload = request.get_json(silent=True) or {}
    coupon_code = payload.get("coupon_code")
    partner_pos_id = payload.get("partner_pos_id")
    if not coupon_code or not partner_pos_id:
        return jsonify({"error": "coupon_code and partner_pos_id are required"}), 400
    result = coupon_service.redeem_coupon(coupon_code, partner_pos_id)
    status = 200 if result.get("redeem_status") == "redeemed" else 400
    return jsonify(result), status


@api.route("/api/user/stats", methods=["GET"])
def get_user_stats() -> Response:
    """사용자의 미션 통계를 조회한다.

    Query Params:
        user_id: 사용자 식별자.

    Returns:
        JSON {total_attempts, success_location, success_atmosphere, total_coupons, history}.
    """
    user_id = request.args.get("user_id", "guest")
    stats = mission_session_service.get_user_stats(user_id)
    return jsonify(stats)


@api.route("/api/coupons", methods=["GET"])
def get_user_coupons() -> Response:
    """사용자가 보유한 모든 쿠폰 목록을 조회한다.

    Query Params:
        user_id: 사용자 식별자 (기본값: 'guest').

    Returns:
        JSON list of coupons.
    """
    user_id = request.args.get("user_id", "guest")
    coupons = coupon_service.get_user_coupons(user_id)
    return jsonify(coupons)
