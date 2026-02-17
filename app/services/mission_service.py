from app.models.blip import check_with_blip, get_visual_context
from app.models.llm import llm_service
from app.services.coupon_service import coupon_service


def run_mission1(user_image, answer):
    """미션1(장소 찾기)을 실행한다.

    BLIP VQA로 이미지 검증 → 성공 시 쿠폰 발급, 실패 시 LLM 힌트 생성.
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


def run_mission2(user_image, answer):
    """미션2(감성 촬영)를 실행한다.

    BLIP으로 시각 컨텍스트 추출 → LLM이 감성 키워드 일치 여부 판단.
    """
    # 1. BLIP으로 시각적 맥락 추출
    context = get_visual_context(user_image)

    # 2. LLM이 맥락과 감성 키워드를 비교 판단
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
