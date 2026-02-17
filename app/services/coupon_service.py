import random
import string
from datetime import datetime


class CouponService:
    """미션 성공 시 쿠폰을 생성/발급하는 서비스"""

    @staticmethod
    def generate_coupon_code():
        """8자리 랜덤 쿠폰 코드를 생성한다."""
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    @staticmethod
    def issue_coupon(mission_type, answer):
        """미션 성공 시 쿠폰을 발급한다.

        Args:
            mission_type: "mission1" 또는 "mission2"
            answer: 미션 정답 (장소명 또는 감성 키워드)

        Returns:
            쿠폰 정보 딕셔너리
        """
        code = CouponService.generate_coupon_code()

        if mission_type == "mission1":
            description = f"{answer} 장소 찾기 미션 완료 쿠폰"
        else:
            description = f"{answer} 감성 사진 촬영 미션 완료 쿠폰"

        return {
            "code": code,
            "description": description,
            "mission_type": mission_type,
            "answer": answer,
            "issued_at": datetime.now().isoformat(),
        }


coupon_service = CouponService()
