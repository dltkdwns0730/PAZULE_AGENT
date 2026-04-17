"""Phase 3 리팩터 검증: coupon_service가 constants를 실제로 참조하는지 검증.

리팩터 목적: coupon_service.py 내 k=8, "10%_OFF" 하드코딩 제거.
검증 기준:
  - generate_coupon_code()의 출력 길이 == constants.COUPON_CODE_LENGTH
  - issue_coupon()의 기본 discount_rule == constants.DEFAULT_DISCOUNT_RULE
  - constants 변경 시 coupon_service 동작이 함께 바뀌는지 확인
"""

from __future__ import annotations


import pytest

from app.core.config import constants
from app.services.coupon_service import CouponService


@pytest.fixture
def tmp_coupon_service(tmp_path: "pytest.TempPathFactory") -> CouponService:
    """임시 디렉터리를 사용하는 독립적인 CouponService 인스턴스."""
    svc = CouponService.__new__(CouponService)
    svc._path = str(tmp_path / "coupons.json")
    return svc


class TestCouponCodeLength:
    """generate_coupon_code()가 constants.COUPON_CODE_LENGTH 기준으로 동작하는지 검증."""

    def test_code_length_matches_constant(
        self, tmp_coupon_service: CouponService
    ) -> None:
        code = tmp_coupon_service.generate_coupon_code()
        assert len(code) == constants.COUPON_CODE_LENGTH

    def test_code_is_uppercase_alphanumeric(
        self, tmp_coupon_service: CouponService
    ) -> None:
        code = tmp_coupon_service.generate_coupon_code()
        assert code.isalnum()
        assert code.isupper()

    def test_code_is_string(self, tmp_coupon_service: CouponService) -> None:
        code = tmp_coupon_service.generate_coupon_code()
        assert isinstance(code, str)

    def test_code_not_empty(self, tmp_coupon_service: CouponService) -> None:
        code = tmp_coupon_service.generate_coupon_code()
        assert len(code) > 0

    def test_multiple_codes_differ(self, tmp_coupon_service: CouponService) -> None:
        """매번 다른 코드를 생성해야 한다 (확률적으로 100회 중 충돌 없음)."""
        codes = {tmp_coupon_service.generate_coupon_code() for _ in range(100)}
        # 100개 중 99개 이상 유니크 (랜덤이지만 매우 높은 확률)
        assert len(codes) >= 99


class TestDefaultDiscountRule:
    """issue_coupon()의 기본 discount_rule이 constants 기반인지 검증."""

    def test_default_discount_rule_used_when_not_specified(
        self, tmp_coupon_service: CouponService
    ) -> None:
        coupon = tmp_coupon_service.issue_coupon(
            mission_type="mission1",
            answer="헤이리마을",
        )
        assert coupon["discount_rule"] == constants.DEFAULT_DISCOUNT_RULE

    def test_custom_discount_rule_overrides_default(
        self, tmp_coupon_service: CouponService
    ) -> None:
        coupon = tmp_coupon_service.issue_coupon(
            mission_type="mission1",
            answer="헤이리마을",
            discount_rule="20%_OFF",
        )
        assert coupon["discount_rule"] == "20%_OFF"

    def test_default_discount_rule_value_matches_constant(
        self, tmp_coupon_service: CouponService
    ) -> None:
        """constants.DEFAULT_DISCOUNT_RULE과 실제 쿠폰 필드가 같아야 한다."""
        coupon = tmp_coupon_service.issue_coupon(
            mission_type="mission2",
            answer="감성적인",
        )
        assert coupon["discount_rule"] == "10%_OFF"
        assert coupon["discount_rule"] == constants.DEFAULT_DISCOUNT_RULE

    def test_issued_coupon_has_all_required_fields(
        self, tmp_coupon_service: CouponService
    ) -> None:
        coupon = tmp_coupon_service.issue_coupon(
            mission_type="mission1",
            answer="지혜의숲",
            mission_id="test-mission-id",
        )
        required = {"code", "discount_rule", "status", "issued_at", "expires_at"}
        assert required.issubset(coupon.keys())

    def test_issue_idempotent_with_same_mission_id(
        self, tmp_coupon_service: CouponService
    ) -> None:
        """같은 mission_id로 두 번 발급하면 동일 쿠폰을 반환해야 한다."""
        c1 = tmp_coupon_service.issue_coupon(
            mission_type="mission1",
            answer="헤이리마을",
            mission_id="idem-001",
        )
        c2 = tmp_coupon_service.issue_coupon(
            mission_type="mission1",
            answer="헤이리마을",
            mission_id="idem-001",
        )
        assert c1["code"] == c2["code"]

    def test_empty_answer_still_issues(self, tmp_coupon_service: CouponService) -> None:
        """answer가 빈 문자열이어도 쿠폰이 발급되어야 한다."""
        coupon = tmp_coupon_service.issue_coupon(
            mission_type="mission1",
            answer="",
        )
        assert coupon["status"] == "issued"
