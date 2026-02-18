import tempfile
import unittest
from pathlib import Path

from app.services.coupon_service import CouponService


class CouponServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.service = CouponService()
        self.service._path = str(Path(self.tmp_dir.name) / "coupons.json")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_issue_coupon_idempotent_by_mission(self):
        coupon1 = self.service.issue_coupon(
            mission_type="mission1",
            answer="지혜의숲 조각상",
            mission_id="m-1",
        )
        coupon2 = self.service.issue_coupon(
            mission_type="mission1",
            answer="지혜의숲 조각상",
            mission_id="m-1",
        )
        self.assertEqual(coupon1["code"], coupon2["code"])

    def test_redeem_coupon_once(self):
        coupon = self.service.issue_coupon(
            mission_type="mission2",
            answer="화사한",
            mission_id="m-2",
        )
        first = self.service.redeem_coupon(coupon["code"], "POS-1")
        second = self.service.redeem_coupon(coupon["code"], "POS-1")

        self.assertEqual(first["redeem_status"], "redeemed")
        self.assertEqual(second["redeem_status"], "already_redeemed")


if __name__ == "__main__":
    unittest.main()
