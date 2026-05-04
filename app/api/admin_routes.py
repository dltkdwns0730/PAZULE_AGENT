"""Admin REST API routes for the PAZULE operations console."""

from __future__ import annotations

import logging

from flask import Blueprint, Response, jsonify, request

from app.services.admin_service import admin_service
from app.security.auth import (
    AuthError,
    AuthPrincipal,
    extract_bearer_token,
    verify_supabase_token,
)

logger = logging.getLogger(__name__)

admin_api = Blueprint("admin_api", __name__)


def _require_auth_principal() -> AuthPrincipal:
    token = extract_bearer_token(request.headers.get("Authorization"))
    return verify_supabase_token(token)


def _auth_error_response(exc: AuthError) -> tuple[Response, int]:
    return jsonify({"error": str(exc)}), 401


def _forbidden_response(reason: str = "forbidden") -> tuple[Response, int]:
    return jsonify({"error": reason}), 403


def _admin_scope_or_error():
    try:
        principal = _require_auth_principal()
        scope = admin_service.resolve_scope(principal)
        if not scope.is_platform_master and not scope.organization_ids:
            raise PermissionError("admin_required")
        return scope, None
    except AuthError as exc:
        return None, _auth_error_response(exc)
    except PermissionError as exc:
        return None, _forbidden_response(str(exc))


@admin_api.route("/api/admin/summary", methods=["GET"])
def admin_summary() -> Response:
    scope, error = _admin_scope_or_error()
    if error:
        return error
    return jsonify(
        admin_service.get_summary(
            scope, organization_id=request.args.get("organization_id") or None
        )
    )


@admin_api.route("/api/admin/organizations", methods=["GET"])
def admin_organizations() -> Response:
    scope, error = _admin_scope_or_error()
    if error:
        return error
    return jsonify(admin_service.list_organizations(scope))


@admin_api.route("/api/admin/mission-sessions", methods=["GET"])
def admin_mission_sessions() -> Response:
    scope, error = _admin_scope_or_error()
    if error:
        return error
    rows = admin_service.list_mission_sessions(
        scope,
        status=request.args.get("status") or None,
        search=request.args.get("search") or None,
        organization_id=request.args.get("organization_id") or None,
    )
    return jsonify(rows)


@admin_api.route("/api/admin/mission-sessions/<mission_id>", methods=["GET"])
def admin_mission_session_detail(mission_id: str) -> Response:
    scope, error = _admin_scope_or_error()
    if error:
        return error
    row = admin_service.get_mission_session(scope, mission_id)
    if not row:
        return jsonify({"error": "mission_session_not_found"}), 404
    return jsonify(row)


@admin_api.route("/api/admin/coupons", methods=["GET"])
def admin_coupons() -> Response:
    scope, error = _admin_scope_or_error()
    if error:
        return error
    rows = admin_service.list_coupons(
        scope,
        status=request.args.get("status") or None,
        search=request.args.get("search") or None,
        organization_id=request.args.get("organization_id") or None,
    )
    return jsonify(rows)


@admin_api.route("/api/admin/coupons/<code>/redeem", methods=["POST"])
def admin_coupon_redeem(code: str) -> Response:
    scope, error = _admin_scope_or_error()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    partner_pos_id = payload.get("partner_pos_id") or "ADMIN-CONSOLE"
    result = admin_service.redeem_coupon(scope, code, partner_pos_id)
    if result.get("redeem_status") == "forbidden":
        return jsonify(result), 403
    status = 200 if result.get("redeem_status") == "redeemed" else 400
    return jsonify(result), status


@admin_api.route("/api/admin/users", methods=["GET"])
def admin_users() -> Response:
    scope, error = _admin_scope_or_error()
    if error:
        return error
    return jsonify(
        admin_service.list_users(
            scope,
            search=request.args.get("search") or None,
            organization_id=request.args.get("organization_id") or None,
        )
    )
