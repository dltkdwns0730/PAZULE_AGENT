"""Node implementations for the mission orchestration graph."""

from __future__ import annotations

import traceback
from typing import Any, Dict, List

from app.core.config import settings
from app.metadata.validator import validate_metadata
from app.models.prompts import build_prompt_bundle
from app.services.mission_session_service import mission_session_service


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


def _append_error(
    errors: List[Dict[str, Any]],
    code: str,
    message: str,
    node: str,
    retryable: bool,
    model: str | None = None,
) -> None:
    """Caller: ?? ?? ???? ???
    Purpose: `_append_error` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: errors: ???? ???? ??; code: ???? ???? ??; message: ???? ???? ??; node: ???? ???? ??; retryable: ???? ???? ??; model: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    payload = {
        "code": code,
        "message": message,
        "node": node,
        "retryable": retryable,
    }
    if model:
        payload["model"] = model
    errors.append(payload)


def gate_keeper(state: Dict[str, Any]) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `gate_keeper` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: state: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    request_context = dict(state.get("request_context", {}))
    artifacts = dict(state.get("artifacts", {}))
    errors = list(state.get("errors", []))
    control_flags = dict(state.get("control_flags", {}))

    image_path = request_context.get("image_path")
    user_id = request_context.get("user_id", "guest")
    if not image_path:
        _append_error(errors, "MISSING_IMAGE", "image_path is required", "gate_keeper", False)
        artifacts["gate_result"] = {"passed": False, "reason": "image_path_missing", "risk_flags": ["missing_image"]}
        control_flags["terminate"] = True
        return {
            "artifacts": artifacts,
            "errors": errors,
            "control_flags": control_flags,
            "messages": ["gate_keeper: missing image_path"],
        }

    metadata_valid = validate_metadata(image_path)
    image_hash = mission_session_service.hash_file(image_path)
    is_duplicate = mission_session_service.is_duplicate_hash_for_user(user_id, image_hash)

    risk_flags: list[str] = []
    if not metadata_valid:
        risk_flags.append("metadata_invalid")
    if is_duplicate:
        risk_flags.append("duplicate_image")

    passed = metadata_valid and not is_duplicate
    reason = "passed" if passed else ",".join(risk_flags) if risk_flags else "blocked"

    if not passed:
        control_flags["terminate"] = True
        _append_error(errors, "GATE_BLOCKED", reason, "gate_keeper", False)

    request_context["image_hash"] = image_hash
    artifacts["gate_result"] = {
        "passed": passed,
        "reason": reason,
        "risk_flags": risk_flags,
        "metadata_valid": metadata_valid,
        "is_duplicate": is_duplicate,
    }
    return {
        "request_context": request_context,
        "artifacts": artifacts,
        "errors": errors,
        "control_flags": control_flags,
        "messages": [f"gate_keeper: {reason}"],
    }


def task_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `task_router` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: state: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    request_context = dict(state.get("request_context", {}))
    mission_type = _normalize_mission_type(request_context.get("mission_type", "location"))
    request_context["mission_type"] = mission_type
    route_decision = {
        "next_node": "model_fanout",
        "reason": f"mission_type={mission_type}",
        "confidence": 1.0,
        "fallback": "finalizer",
    }
    return {
        "request_context": request_context,
        "route_decision": route_decision,
        "messages": [f"task_router: {mission_type}"],
    }


def _select_models(mission_type: str, override: str | None = None) -> list[str]:
    """Caller: ?? ?? ???? ???
    Purpose: `_select_models` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: mission_type: ???? ???? ??; override: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    if override:
        mode = override.lower().strip()
        if mode == "ensemble":
            return (
                settings.location_ensemble_models
                if mission_type == "location"
                else settings.atmosphere_ensemble_models
            )
        return [mode]

    if mission_type == "location":
        mode = settings.MODEL_SELECTION_LOCATION.lower().strip()
        if mode == "ensemble":
            return settings.location_ensemble_models
        return [mode]
    mode = settings.MODEL_SELECTION_ATMOSPHERE.lower().strip()
    if mode == "ensemble":
        return settings.atmosphere_ensemble_models
    return [mode]


def _invoke_model(model_name: str, mission_type: str, image_path: str, answer: str, prompt_bundle):
    """Caller: ?? ?? ???? ???
    Purpose: `_invoke_model` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: model_name: ???? ???? ??; mission_type: ???? ???? ??; image_path: ???? ???? ??; answer: ???? ???? ??; prompt_bundle: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    model_name = model_name.lower().strip()
    if model_name == "blip":
        from app.models.blip import probe_with_blip_atmosphere, probe_with_blip_location

        if mission_type == "location":
            return probe_with_blip_location(image_path, answer, prompt_bundle)
        return probe_with_blip_atmosphere(image_path, answer, prompt_bundle)
    if model_name == "clip":
        from app.models.clip import probe_with_clip

        return probe_with_clip(mission_type, image_path, answer, prompt_bundle)
    if model_name == "qwen":
        from app.models.qwen_vl import probe_with_qwen

        return probe_with_qwen(mission_type, image_path, answer, prompt_bundle)
    if model_name == "siglip2":
        from app.models.siglip2 import probe_with_siglip2

        return probe_with_siglip2(mission_type, image_path, answer, prompt_bundle)
    raise ValueError(f"Unsupported model: {model_name}")


def model_fanout(state: Dict[str, Any]) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `model_fanout` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: state: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    request_context = dict(state.get("request_context", {}))
    artifacts = dict(state.get("artifacts", {}))
    errors = list(state.get("errors", []))
    mission_type = _normalize_mission_type(request_context.get("mission_type", "location"))
    image_path = request_context.get("image_path")
    answer = request_context.get("answer")

    selected_models = _select_models(
        mission_type, request_context.get("model_selection")
    )
    prompt_bundle = build_prompt_bundle(mission_type, answer)
    votes: list[Dict[str, Any]] = []

    for model_name in selected_models:
        try:
            vote = _invoke_model(model_name, mission_type, image_path, answer, prompt_bundle)
            votes.append(vote)
        except Exception as exc:
            _append_error(
                errors,
                "MODEL_FAILURE",
                f"{model_name}: {exc}",
                "model_fanout",
                True,
                model=model_name,
            )
            traceback.print_exc()

    artifacts["prompt_bundle"] = prompt_bundle
    artifacts["selected_models"] = selected_models
    artifacts["model_votes"] = votes

    if not votes:
        _append_error(errors, "NO_MODEL_VOTES", "No models produced output", "model_fanout", False)

    return {
        "artifacts": artifacts,
        "errors": errors,
        "messages": [f"model_fanout: {','.join(selected_models)}"],
    }


def evidence_aggregator(state: Dict[str, Any]) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `evidence_aggregator` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: state: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    request_context = dict(state.get("request_context", {}))
    artifacts = dict(state.get("artifacts", {}))
    mission_type = _normalize_mission_type(request_context.get("mission_type", "location"))
    votes = list(artifacts.get("model_votes", []))

    if mission_type == "location":
        weights = {"blip": 0.45, "qwen": 0.35, "clip": 0.2, "siglip2": 0.1}
    else:
        weights = {"siglip2": 0.45, "qwen": 0.35, "blip": 0.15, "clip": 0.05}

    weighted_sum = 0.0
    total_weight = 0.0
    labels = set()
    scores = []

    for vote in votes:
        model = vote.get("model")
        score = float(vote.get("score", 0.0))
        weight = weights.get(model, 0.1)
        weighted_sum += score * weight
        total_weight += weight
        labels.add(vote.get("label"))
        scores.append(score)

    merged_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    threshold = (
        settings.LOCATION_PASS_THRESHOLD
        if mission_type == "location"
        else settings.ATMOSPHERE_PASS_THRESHOLD
    )
    merged_label = "match" if merged_score >= threshold else "mismatch"
    conflict = len(labels) > 1 and (max(scores) - min(scores) >= 0.35 if scores else False)

    artifacts["ensemble_result"] = {
        "mission_type": mission_type,
        "merged_score": round(merged_score, 4),
        "merged_label": merged_label,
        "threshold": threshold,
        "conflict": conflict,
        "vote_count": len(votes),
    }
    return {"artifacts": artifacts, "messages": [f"evidence_aggregator: score={merged_score:.2f}"]}


def decision_engine(state: Dict[str, Any]) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `decision_engine` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: state: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    artifacts = dict(state.get("artifacts", {}))
    control_flags = dict(state.get("control_flags", {}))
    errors = list(state.get("errors", []))

    gate_result = artifacts.get("gate_result", {})
    ensemble = artifacts.get("ensemble_result", {})

    if not gate_result.get("passed"):
        judgment = {
            "success": False,
            "reason": gate_result.get("reason", "gate_blocked"),
            "confidence": 0.0,
            "mission_type": ensemble.get("mission_type", "location"),
        }
        artifacts["judgment"] = judgment
        return {"artifacts": artifacts, "messages": ["decision_engine: gate blocked"]}

    merged_score = float(ensemble.get("merged_score", 0.0))
    threshold = float(ensemble.get("threshold", 1.0))
    conflict = bool(ensemble.get("conflict"))
    success = merged_score >= threshold
    reason = "score_passed" if success else "score_below_threshold"

    if conflict and merged_score < (threshold + 0.08):
        success = False
        reason = "model_conflict_requires_retry"
        control_flags["manual_review"] = True
        _append_error(errors, "MODEL_CONFLICT", reason, "decision_engine", False)

    artifacts["judgment"] = {
        "success": success,
        "reason": reason,
        "confidence": round(merged_score, 4),
        "mission_type": ensemble.get("mission_type", "location"),
        "conflict": conflict,
    }
    return {
        "artifacts": artifacts,
        "errors": errors,
        "control_flags": control_flags,
        "messages": [f"decision_engine: {reason}"],
    }


def coupon_policy_engine(state: Dict[str, Any]) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `coupon_policy_engine` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: state: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    artifacts = dict(state.get("artifacts", {}))
    judgment = artifacts.get("judgment", {})
    gate = artifacts.get("gate_result", {})
    risk_flags = set(gate.get("risk_flags", []))

    eligible = bool(judgment.get("success")) and "duplicate_image" not in risk_flags
    deny_reason = None if eligible else ("duplicate_image" if "duplicate_image" in risk_flags else judgment.get("reason"))

    artifacts["coupon_decision"] = {
        "eligible": eligible,
        "deny_reason": deny_reason,
        "discount_rule": "10%_OFF",
    }
    return {"artifacts": artifacts, "messages": [f"coupon_policy_engine: eligible={eligible}"]}


def finalizer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `finalizer` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: state: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    request_context = dict(state.get("request_context", {}))
    artifacts = dict(state.get("artifacts", {}))
    errors = list(state.get("errors", []))
    gate = artifacts.get("gate_result", {})
    votes = artifacts.get("model_votes", [])
    ensemble = artifacts.get("ensemble_result", {})
    judgment = artifacts.get("judgment", {})
    coupon_decision = artifacts.get("coupon_decision", {"eligible": False, "deny_reason": None})

    mission_type = request_context.get("mission_type", "location")
    legacy_mission_type = "photo" if mission_type == "atmosphere" else mission_type

    if not gate.get("passed"):
        msg = "제출이 정책을 통과하지 못했습니다."
        final_data = {
            "success": False,
            "error": gate.get("reason", "gate_blocked"),
            "message": msg,
            "missionType": legacy_mission_type,
            "decision_trace": {"route_decision": state.get("route_decision"), "errors": errors},
            "confidence": 0.0,
            "model_votes": votes,
        }
        return {
            "final_response": {"ui_theme": "error", "message": msg, "data": final_data},
            "messages": ["finalizer: blocked"],
        }

    success = bool(judgment.get("success"))
    if success:
        message = "미션 성공! 쿠폰 발급 단계로 이동할 수 있습니다."
        final_data = {
            "success": True,
            "message": message,
            "missionType": legacy_mission_type,
            "couponEligible": bool(coupon_decision.get("eligible")),
            "confidence": judgment.get("confidence", ensemble.get("merged_score", 0.0)),
            "decision_trace": {
                "route_decision": state.get("route_decision"),
                "judgment": judgment,
                "coupon_decision": coupon_decision,
            },
            "model_votes": votes,
        }
        return {
            "final_response": {"ui_theme": "confetti", "message": message, "data": final_data},
            "messages": ["finalizer: success"],
        }

    failure_reason = judgment.get("reason", "판정 실패")
    hint = None
    if votes:
        best_vote = sorted(votes, key=lambda x: x.get("score", 0.0), reverse=True)[0]
        hint = best_vote.get("reason")

    message = "미션 조건이 충분히 충족되지 않았습니다. 다시 시도해 주세요."
    final_data = {
        "success": False,
        "message": message,
        "missionType": legacy_mission_type,
        "hint": hint or failure_reason,
        "confidence": judgment.get("confidence", 0.0),
        "decision_trace": {"judgment": judgment, "coupon_decision": coupon_decision},
        "model_votes": votes,
    }
    return {
        "final_response": {"ui_theme": "encouragement", "message": message, "data": final_data},
        "messages": ["finalizer: fail"],
    }
