"""미션 서비스 모듈: 장소 찾기 및 감성 촬영 미션 실행 로직."""

from __future__ import annotations

import logging
from typing import Any

from app.models.blip import check_with_blip, get_visual_context
from app.models.llm import llm_service
from app.services.coupon_service import coupon_service

logger = logging.getLogger(__name__)


def run_mission1(user_image: str, answer: str) -> dict[str, Any]:
    """미션1(장소 찾기)을 실행한다.

    BLIP VQA로 이미지 검증 → 성공 시 쿠폰 발급, 실패 시 LLM 힌트 생성.

    Args:
        user_image: 사용자가 업로드한 이미지 파일 경로.
        answer: 미션 정답 키워드.

    Returns:
        미션 실행 결과 딕셔너리. 성공 시 'coupon' 포함, 실패 시 'hint' 포함.
    """
    mission_result, blip_info = check_with_blip(user_image, answer)

    if mission_result:
        coupon = coupon_service.issue_coupon("mission1", answer)
        return {"success": True, "coupon": coupon}

    hint = llm_service.generate_blip_hint(answer, blip_info)
    return {
        "success": False,
        "hint": hint,
        "message": "장소를 다시 찾아보세요!",
    }


def run_mission2(user_image: str, answer: str) -> dict[str, Any]:
    """미션2(감성 촬영)를 실행한다.

    BLIP으로 시각 컨텍스트 추출 → LLM이 감성 키워드 일치 여부 판단.

    Args:
        user_image: 사용자가 업로드한 이미지 파일 경로.
        answer: 미션 감성 키워드.

    Returns:
        미션 실행 결과 딕셔너리. 성공 시 'coupon' 포함, 실패 시 'hint' 포함.
    """
    context = get_visual_context(user_image)
    verification = llm_service.verify_mood(answer, context)

    if verification.get("success"):
        coupon = coupon_service.issue_coupon("mission2", answer)
        return {
            "success": True,
            "coupon": coupon,
            "message": verification.get("reason", "감성 분석 성공!"),
        }

    return {
        "success": False,
        "hint": verification.get("reason", "분위기가 잘 느껴지지 않아요."),
        "message": "감성이 담긴 사진을 다시 찍어보세요!",
    }
