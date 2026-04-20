"""Node implementations for the mission orchestration graph."""

from __future__ import annotations

import concurrent.futures
import logging
import time
import traceback
from typing import Any

from app.core.config import constants, settings
from app.core.utils import normalize_mission_type
from app.metadata.validator import validate_metadata
from app.models.prompts import build_prompt_bundle
from app.services.mission_session_service import mission_session_service

logger = logging.getLogger(__name__)

# 멀티스레딩 환경(ThreadPoolExecutor)에서 transformers 라이브러리의 지연 로딩 이슈를 방지하기 위해
# 메인 스레드에서 주요 클래스들을 미리 임포트하여 캐싱한다.
try:
    from transformers import (  # noqa: F401
        AutoModel,
        AutoProcessor,
        BlipForQuestionAnswering,
        BlipProcessor,
    )

    logger.debug("Transformers core classes pre-loaded in main thread.")
except ImportError:
    logger.warning(
        "Transformers classes not pre-loaded; might cause issues in sub-threads."
    )


# Local helper _normalize_mission_type removed in favor of app.core.utils.normalize_mission_type


def _append_error(
    errors: list[dict[str, Any]],
    code: str,
    message: str,
    node: str,
    retryable: bool,
    model: str | None = None,
) -> None:
    """파이프라인 실행 중 발생한 오류를 state errors 배열에 추가한다.

    Args:
        errors: 누적 오류 리스트 (in-place 수정).
        code: 에러 코드 문자열.
        message: 사람이 읽을 수 있는 에러 메시지.
        node: 오류가 발생한 노드 이름.
        retryable: 재시도 가능 여부.
        model: (선택) 오류를 발생시킨 모델 이름.
    """
    payload: dict[str, Any] = {
        "code": code,
        "message": message,
        "node": node,
        "retryable": retryable,
    }
    if model:
        payload["model"] = model
    errors.append(payload)


# ── validator 헬퍼 ──────────────────────────────────────────────────────────


def _check_image_presence(
    image_path: str | None,
    artifacts: dict[str, Any],
    errors: list[dict[str, Any]],
    control_flags: dict[str, Any],
) -> bool:
    """이미지 경로 존재 여부를 확인한다. 누락 시 terminate 플래그를 설정한다.

    Args:
        image_path: 검사할 이미지 경로 (None이면 실패).
        artifacts: 파이프라인 artifacts dict (in-place 수정).
        errors: 누적 에러 리스트 (in-place 수정).
        control_flags: 파이프라인 제어 플래그 dict (in-place 수정).

    Returns:
        이미지 경로가 유효하면 True, 없으면 False.
    """
    if image_path:
        return True
    logger.warning("[validator] BLOCKED: image_path missing")
    _append_error(errors, "MISSING_IMAGE", "image_path is required", "validator", False)
    artifacts["gate_result"] = {
        "passed": False,
        "reason": "image_path_missing",
        "risk_flags": ["missing_image"],
    }
    control_flags["terminate"] = True
    return False


def _check_metadata(
    image_path: str,
    artifacts: dict[str, Any],
) -> bool:
    """EXIF/GPS 메타데이터 유효성을 검증한다. SKIP_METADATA_VALIDATION 설정을 반영한다.

    Args:
        image_path: 검사할 이미지 파일 경로.
        artifacts: 파이프라인 artifacts dict (메타데이터 skip 여부 기록용).

    Returns:
        검증 통과 또는 skip 시 True, 실패 시 False.
    """
    if settings.SKIP_METADATA_VALIDATION:
        logger.debug("[validator] SKIP_METADATA_VALIDATION=true → GPS·날짜 검증 건너뜀")
        artifacts["metadata_check_skipped"] = True
        return True
    logger.debug("[validator] GPS·날짜 EXIF 검증 중...")
    result = validate_metadata(image_path)
    logger.debug("[validator] metadata_valid=%s", result)
    artifacts["metadata_check_skipped"] = False
    return result


def _check_duplicate(
    user_id: str,
    image_path: str,
    request_context: dict[str, Any],
) -> tuple[str, bool]:
    """이미지 해시를 계산하고 동일 사용자의 중복 제출 여부를 검사한다.

    Args:
        user_id: 사용자 식별자.
        image_path: 해시를 계산할 이미지 파일 경로.
        request_context: 파이프라인 request context dict (image_hash 기록용).

    Returns:
        (image_hash, is_duplicate) 튜플.
    """
    image_hash = mission_session_service.hash_file(image_path)
    is_duplicate = mission_session_service.is_duplicate_hash_for_user(
        user_id, image_hash
    )
    logger.debug(
        "[validator] image_hash=%s...  is_duplicate=%s", image_hash[:12], is_duplicate
    )
    request_context["image_hash"] = image_hash
    if settings.SKIP_METADATA_VALIDATION and is_duplicate:
        logger.debug(
            "[validator] SKIP_METADATA_VALIDATION=true → 중복 이미지 제출 검증 건너뜀"
        )
        is_duplicate = False
    return image_hash, is_duplicate


# ── evaluator 헬퍼 ─────────────────────────────────────────────────────────


def _build_bypass_votes(selected_models: list[str]) -> list[dict[str, Any]]:
    """BYPASS_MODEL_VALIDATION 모드 전용: score=1.0 가짜 투표 목록을 반환한다.

    Args:
        selected_models: 우회 처리할 모델 이름 리스트.

    Returns:
        각 모델에 대해 score=1.0인 투표 딕셔너리 리스트.
    """
    return [
        {"model": m, "score": 1.0, "label": "match", "reason": "bypass_mode"}
        for m in selected_models
    ]


def _process_model_future(
    future: concurrent.futures.Future,
    model_name: str,
    errors: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """단일 모델 future 결과를 처리하고 에러 시 None을 반환한다.

    Args:
        future: 모델 추론 Future 객체.
        model_name: 모델 식별자 (로그·에러 기록용).
        errors: 누적 에러 리스트 (in-place 수정).

    Returns:
        모델 투표 딕셔너리, 실패 또는 타임아웃 시 None.
    """
    timeout = settings.API_TIMEOUT_SECONDS + constants.MODEL_TIMEOUT_BUFFER_SECONDS
    try:
        start = time.time()
        vote = future.result(timeout=timeout)
        elapsed = time.time() - start
        logger.info("[Evaluator/%s] 완료 (%.2f초)", model_name, elapsed)
        return vote
    except concurrent.futures.TimeoutError:
        _append_error(
            errors,
            "MODEL_TIMEOUT",
            f"{model_name} execution timed out",
            "evaluator",
            False,
            model=model_name,
        )
        logger.warning("[Evaluator/%s] 시간 초과 (Timeout)", model_name)
        return None
    except Exception as exc:
        _append_error(
            errors,
            "MODEL_FAILURE",
            f"{model_name}: {exc}",
            "evaluator",
            True,
            model=model_name,
        )
        logger.warning("[Evaluator/%s] 실패: %s", model_name, exc)
        logger.debug(traceback.format_exc())
        return None


# ── 노드 함수 ──────────────────────────────────────────────────────────────


def validator(state: dict[str, Any]) -> dict[str, Any]:
    """[검증기] 이미지 누락·메타데이터 유효성·중복 제출을 1차 방어한다.

    Args:
        state: 파이프라인 상태 딕셔너리.

    Returns:
        갱신된 부분 상태 딕셔너리 (request_context, artifacts, errors, control_flags, messages).
    """
    request_context = dict(state.get("request_context", {}))
    artifacts = dict(state.get("artifacts", {}))
    errors = list(state.get("errors", []))
    control_flags = dict(state.get("control_flags", {}))

    image_path = request_context.get("image_path")
    user_id = request_context.get("user_id", "guest")
    mission_type = request_context.get("mission_type", "?")

    logger.info(
        "[validator] user=%s  mission_type=%s  image_path=%s",
        user_id,
        mission_type,
        image_path,
    )

    if not _check_image_presence(image_path, artifacts, errors, control_flags):
        return {
            "artifacts": artifacts,
            "errors": errors,
            "control_flags": control_flags,
            "messages": ["validator: missing image_path"],
        }

    metadata_valid = _check_metadata(image_path, artifacts)
    image_hash, is_duplicate = _check_duplicate(user_id, image_path, request_context)

    risk_flags: list[str] = []
    if not metadata_valid:
        risk_flags.append("metadata_invalid")
    if is_duplicate:
        risk_flags.append("duplicate_image")

    passed = metadata_valid and not is_duplicate
    reason = "passed" if passed else (",".join(risk_flags) if risk_flags else "blocked")

    if not passed:
        control_flags["terminate"] = True
        _append_error(errors, "GATE_BLOCKED", reason, "validator", False)
        logger.warning("[validator] BLOCKED: %s", reason)
    else:
        logger.info("[validator] PASSED")

    artifacts["gate_result"] = {
        "passed": passed,
        "reason": reason,
        "risk_flags": risk_flags,
        "metadata_valid": metadata_valid,
        "is_duplicate": is_duplicate,
        "metadata_check_skipped": settings.SKIP_METADATA_VALIDATION,
    }
    return {
        "request_context": request_context,
        "artifacts": artifacts,
        "errors": errors,
        "control_flags": control_flags,
        "messages": [f"validator: {reason}"],
    }


def router(state: dict[str, Any]) -> dict[str, Any]:
    """[분배기] 미션 종류에 따라 평가기(Evaluator)로 트래픽을 분배할 준비를 한다.

    Args:
        state: 파이프라인 상태 딕셔너리.

    Returns:
        갱신된 부분 상태 딕셔너리 (request_context, route_decision, messages).
    """
    request_context = dict(state.get("request_context", {}))
    mission_type = normalize_mission_type(
        request_context.get("mission_type", "location")
    )
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
        "messages": [f"router: {mission_type}"],
    }


def _select_models(mission_type: str, override: str | None = None) -> list[str]:
    """미션 유형과 커스텀 오버라이드 값에 기반하여 투입할 비전 모델 리스트를 반환한다.

    Args:
        mission_type: 'location' | 'atmosphere'.
        override: 클라이언트 지정 모델 오버라이드 문자열 (선택).

    Returns:
        사용할 모델 이름 리스트.
    """
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


def _invoke_model(
    model_name: str,
    mission_type: str,
    image_path: str,
    answer: str,
    prompt_bundle: Any,
) -> dict[str, Any]:
    """ModelRegistry를 통해 모델 프로브를 조회하고 실행한다.

    Args:
        model_name: 실행할 모델 식별자.
        mission_type: 'location' | 'atmosphere'.
        image_path: 평가할 이미지 파일 경로.
        answer: 오늘의 정답 키워드.
        prompt_bundle: 모델에 전달할 프롬프트 번들.

    Returns:
        모델 투표 딕셔너리 (score, label, reason 포함).
    """
    from app.models.model_registry import ModelRegistry

    registry = ModelRegistry.get_instance()
    probe = registry.get(model_name)
    return probe.probe(mission_type, image_path, answer, prompt_bundle)


def evaluator(state: dict[str, Any]) -> dict[str, Any]:
    """[평가기] 선택된 모델 앙상블을 병렬 실행하고 각 AI 투표를 수집한다.

    Args:
        state: 파이프라인 상태 딕셔너리.

    Returns:
        갱신된 부분 상태 딕셔너리 (artifacts, errors, messages).
    """
    request_context = dict(state.get("request_context", {}))
    artifacts = dict(state.get("artifacts", {}))
    errors = list(state.get("errors", []))
    mission_type = normalize_mission_type(
        request_context.get("mission_type", "location")
    )
    image_path = request_context.get("image_path")
    answer = request_context.get("answer")

    selected_models = _select_models(
        mission_type, request_context.get("model_selection")
    )
    prompt_bundle = build_prompt_bundle(mission_type, answer)

    if settings.BYPASS_MODEL_VALIDATION:
        logger.info(
            "[evaluator] BYPASS_MODEL_VALIDATION=true → 모델 추론 건너뜀, score=1.0 강제"
        )
        artifacts["prompt_bundle"] = prompt_bundle
        artifacts["selected_models"] = selected_models
        artifacts["model_votes"] = _build_bypass_votes(selected_models)
        return {
            "artifacts": artifacts,
            "errors": errors,
            "messages": [f"evaluator: bypass ({','.join(selected_models)})"],
        }

    logger.info(
        "[evaluator] %d개 모델 동시 평가 시작: %s",
        len(selected_models),
        ",".join(selected_models),
    )
    votes: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(selected_models)
    ) as executor:
        future_to_model = {
            executor.submit(
                _invoke_model,
                model_name,
                mission_type,
                image_path,
                answer,
                prompt_bundle,
            ): model_name
            for model_name in selected_models
        }
        for future in concurrent.futures.as_completed(future_to_model):
            model_name = future_to_model[future]
            vote = _process_model_future(future, model_name, errors)
            if vote is not None:
                votes.append(vote)

    artifacts["prompt_bundle"] = prompt_bundle
    artifacts["selected_models"] = selected_models
    artifacts["model_votes"] = votes

    if not votes:
        _append_error(
            errors, "NO_MODEL_VOTES", "No models produced output", "evaluator", False
        )

    return {
        "artifacts": artifacts,
        "errors": errors,
        "messages": [f"evaluator: {','.join(selected_models)}"],
    }


def aggregator(state: dict[str, Any]) -> dict[str, Any]:
    """[취합기] 다수의 모델 점수를 가중치 스펙에 맞춰 대표 점수로 병합한다.

    모델 간 이견이 ENSEMBLE_CONFLICT_THRESHOLD 이상이면 conflict 플래그를 설정한다.

    Args:
        state: 파이프라인 상태 딕셔너리.

    Returns:
        갱신된 부분 상태 딕셔너리 (artifacts, messages).
    """
    request_context = dict(state.get("request_context", {}))
    artifacts = dict(state.get("artifacts", {}))
    mission_type = normalize_mission_type(
        request_context.get("mission_type", "location")
    )
    votes = list(artifacts.get("model_votes", []))

    weights = (
        constants.LOCATION_MODEL_WEIGHTS
        if mission_type == "location"
        else constants.ATMOSPHERE_MODEL_WEIGHTS
    )

    weighted_sum = 0.0
    total_weight = 0.0
    labels: set[str] = set()
    scores: list[float] = []

    for vote in votes:
        model = vote.get("model")
        score = float(vote.get("score", 0.0))
        weight = weights.get(model, constants.DEFAULT_MODEL_WEIGHT)
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
    conflict = len(labels) > 1 and (
        max(scores) - min(scores) >= constants.ENSEMBLE_CONFLICT_THRESHOLD
        if scores
        else False
    )

    logger.info(
        "[aggregator] votes=%d  merged_score=%.4f  threshold=%s  label=%s  conflict=%s",
        len(votes),
        merged_score,
        threshold,
        merged_label,
        conflict,
    )

    artifacts["ensemble_result"] = {
        "mission_type": mission_type,
        "merged_score": round(merged_score, 4),
        "merged_label": merged_label,
        "threshold": threshold,
        "conflict": conflict,
        "vote_count": len(votes),
    }
    return {
        "artifacts": artifacts,
        "messages": [f"aggregator: score={merged_score:.2f}"],
    }


def judge(state: dict[str, Any]) -> dict[str, Any]:
    """[심판] 앙상블 점수를 기반으로 미션 합격 여부를 최종 확정한다.

    conflict가 있고 점수가 COUNCIL_BORDERLINE_MARGIN 이내이면 council 검토를 요청한다.

    Args:
        state: 파이프라인 상태 딕셔너리.

    Returns:
        갱신된 부분 상태 딕셔너리 (artifacts, errors, control_flags, messages).
    """
    artifacts = dict(state.get("artifacts", {}))
    control_flags = dict(state.get("control_flags", {}))
    errors = list(state.get("errors", []))

    gate_result = artifacts.get("gate_result", {})
    ensemble = artifacts.get("ensemble_result", {})

    merged_score = float(ensemble.get("merged_score", 0.0))
    threshold = float(ensemble.get("threshold", 1.0))
    conflict = bool(ensemble.get("conflict"))

    if not gate_result.get("passed"):
        logger.info("[judge] gate not passed → forced fail")
        judgment = {
            "success": False,
            "reason": gate_result.get("reason", "gate_blocked"),
            "confidence": 0.0,
            "mission_type": ensemble.get("mission_type", "location"),
        }
        artifacts["judgment"] = judgment
        return {"artifacts": artifacts, "messages": ["judge: gate blocked"]}

    success = merged_score >= threshold
    reason = "score_passed" if success else "score_below_threshold"
    logger.info(
        "[judge] score=%.4f  threshold=%s  pass=%s", merged_score, threshold, success
    )

    borderline = threshold + settings.COUNCIL_BORDERLINE_MARGIN
    if conflict and merged_score < borderline:
        success = False
        reason = "model_conflict_requires_retry"
        control_flags["manual_review"] = True
        _append_error(errors, "MODEL_CONFLICT", reason, "judge", False)
        logger.warning("[judge] conflict detected → overridden to fail")

    council_verdict = artifacts.get("council_verdict")
    council_override = False
    if council_verdict:
        council_approved = bool(council_verdict.get("approved"))
        if council_approved != success:
            council_override = True
            success = council_approved
            reason = f"council_override: {council_verdict.get('reason', 'N/A')}"
            logger.warning("[judge] council override → success=%s", success)
        if council_verdict.get("escalated"):
            control_flags["manual_review"] = True

    logger.info("[judge] FINAL: success=%s  reason=%s", success, reason)

    artifacts["judgment"] = {
        "success": success,
        "reason": reason,
        "confidence": round(merged_score, 4),
        "mission_type": ensemble.get("mission_type", "location"),
        "conflict": conflict,
        "council_override": council_override,
    }
    return {
        "artifacts": artifacts,
        "errors": errors,
        "control_flags": control_flags,
        "messages": [f"judge: {reason}"],
    }


def policy(state: dict[str, Any]) -> dict[str, Any]:
    """[정책] AI 판단 통과 여부와 리스크 플래그를 종합해 쿠폰 지급 자격을 결정한다.

    Args:
        state: 파이프라인 상태 딕셔너리.

    Returns:
        갱신된 부분 상태 딕셔너리 (artifacts, messages).
    """
    artifacts = dict(state.get("artifacts", {}))
    judgment = artifacts.get("judgment", {})
    gate = artifacts.get("gate_result", {})
    risk_flags = set(gate.get("risk_flags", []))

    eligible = bool(judgment.get("success")) and "duplicate_image" not in risk_flags
    deny_reason = (
        None
        if eligible
        else (
            "duplicate_image"
            if "duplicate_image" in risk_flags
            else judgment.get("reason")
        )
    )

    logger.info("[policy] coupon_eligible=%s  deny=%s", eligible, deny_reason)

    artifacts["coupon_decision"] = {
        "eligible": eligible,
        "deny_reason": deny_reason,
        "discount_rule": constants.DEFAULT_DISCOUNT_RULE,
    }
    return {"artifacts": artifacts, "messages": [f"policy: eligible={eligible}"]}


def _generate_retry_hint(answer: str, static_hint: str, mission_type: str) -> str:
    """실패 시 재시도 힌트를 LLM으로 생성한다.

    정답 키워드·실패 이유를 직접 언급하지 않고, 정답 장소의 분위기와
    기존 정적 힌트의 감성 톤을 조합하여 자연스러운 한국어 문장을 반환한다.

    Args:
        answer: 미션 정답 키워드 (장소명 또는 감성어).
        static_hint: answer.json에 미리 작성된 정적 힌트 문자열.
        mission_type: 미션 유형 ('location' | 'atmosphere').

    Returns:
        생성된 한국어 힌트 문자열. LLM 호출 실패 시 static_hint 반환.
    """
    from app.models.llm import LLMService

    try:
        svc = LLMService()
        return svc.generate_blip_hint(
            answer=answer,
            static_hint=static_hint,
            mission_type=mission_type,
        )
    except Exception as exc:
        logger.warning("[responder] LLM 힌트 생성 실패, 정적 힌트로 폴백: %s", exc)
        return static_hint or "장소를 다시 한번 살펴보세요."


def responder(state: dict[str, Any]) -> dict[str, Any]:
    """[응답기] 파이프라인 State를 프론트엔드 API DTO 포맷으로 조립한다.

    Args:
        state: 파이프라인 상태 딕셔너리.

    Returns:
        갱신된 부분 상태 딕셔너리 (final_response, messages).
    """
    request_context = dict(state.get("request_context", {}))
    artifacts = dict(state.get("artifacts", {}))
    errors = list(state.get("errors", []))
    gate = artifacts.get("gate_result", {})
    votes = artifacts.get("model_votes", [])
    ensemble = artifacts.get("ensemble_result", {})
    judgment = artifacts.get("judgment", {})
    coupon_decision = artifacts.get(
        "coupon_decision", {"eligible": False, "deny_reason": None}
    )

    mission_type = request_context.get("mission_type", "location")
    legacy_mission_type = "photo" if mission_type == "atmosphere" else mission_type

    success = bool(judgment.get("success")) if gate.get("passed") else False
    icon = "🎉" if success else "❌"
    logger.info("[responder] %s %s", icon, "SUCCESS" if success else "FAIL")
    if errors:
        logger.debug("[responder] errors: %s", [e.get("code") for e in errors])

    if not gate.get("passed"):
        msg = "제출이 정책을 통과하지 못했습니다."
        final_data = {
            "success": False,
            "error": gate.get("reason", "gate_blocked"),
            "message": msg,
            "missionType": legacy_mission_type,
            "decision_trace": {
                "route_decision": state.get("route_decision"),
                "errors": errors,
            },
            "confidence": 0.0,
            "model_votes": votes,
        }
        return {
            "final_response": {"ui_theme": "error", "message": msg, "data": final_data},
            "messages": ["responder: blocked"],
        }

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
            "final_response": {
                "ui_theme": "confetti",
                "message": message,
                "data": final_data,
            },
            "messages": ["responder: success"],
        }

    answer = request_context.get("answer", "")
    static_hint = request_context.get("static_hint", "")

    hint = _generate_retry_hint(answer, static_hint, mission_type)

    message = "미션 조건이 충분히 충족되지 않았습니다. 다시 시도해 주세요."
    final_data = {
        "success": False,
        "message": message,
        "missionType": legacy_mission_type,
        "hint": hint,
        "confidence": judgment.get("confidence", 0.0),
        "decision_trace": {"judgment": judgment, "coupon_decision": coupon_decision},
        "model_votes": votes,
    }
    return {
        "final_response": {
            "ui_theme": "encouragement",
            "message": message,
            "data": final_data,
        },
        "messages": ["responder: fail"],
    }
