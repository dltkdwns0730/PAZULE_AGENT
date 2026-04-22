"""CouponService 확장 단위 테스트.

기존 test_coupon_service.py의 2개 테스트를 보완한다.

검증 대상:
  - _read_all: JSON 파싱 오류 시 {"coupons": []} 반환 (라인 34-35)
  - _find_by_code: 존재/미존재 (라인 69-73)
  - redeem_coupon: not_found / expired (라인 165, 175-178)
  - generate_coupon_code: 길이 및 문자셋
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.coupon_service import CouponService


@pytest.fixture()
def svc(tmp_path: Path) -> CouponService:
    """tmp_path에 격리된 CouponService 인스턴스."""
    with patch("app.services.coupon_service.settings") as mock_settings:
        mock_settings.DATA_DIR = str(tmp_path)
        service = CouponService()
    service._path = str(tmp_path / "coupons.json")
    return service


def _issue(svc: CouponService, mid: str = "m-1") -> dict:
    return svc.issue_coupon("mission1", "지혜의숲 조각상", mission_id=mid)


# ── _read_all: JSON 파싱 오류 ────────────────────────────────────────────────


class TestReadAllException:
    def test_corrupted_json_returns_empty_coupons(self, svc: CouponService) -> None:
        Path(svc._path).write_text("NOT VALID JSON !!!", encoding="utf-8")
        result = svc._read_all()
        assert result == {"coupons": []}

    def test_empty_file_returns_empty_coupons(self, svc: CouponService) -> None:
        Path(svc._path).write_bytes(b"")
        result = svc._read_all()
        assert result == {"coupons": []}


# ── _find_by_code ────────────────────────────────────────────────────────────


class TestFindByCode:
    def test_existing_code_returns_coupon(self, svc: CouponService) -> None:
        coupon = _issue(svc)
        found = svc._find_by_code(coupon["code"])
        assert found is not None
        assert found["code"] == coupon["code"]

    def test_nonexistent_code_returns_none(self, svc: CouponService) -> None:
        _issue(svc)
        assert svc._find_by_code("ZZZZZZZZ") is None

    def test_empty_store_returns_none(self, svc: CouponService) -> None:
        assert svc._find_by_code("ANY") is None


# ── redeem_coupon: not_found ─────────────────────────────────────────────────


class TestRedeemNotFound:
    def test_unknown_code_returns_not_found(self, svc: CouponService) -> None:
        result = svc.redeem_coupon("BADCODE1", "POS-1")
        assert result["redeem_status"] == "not_found"
        assert "message" in result

    def test_not_found_has_no_coupon_key(self, svc: CouponService) -> None:
        result = svc.redeem_coupon("BADCODE1", "POS-1")
        assert "coupon" not in result


# ── redeem_coupon: expired ───────────────────────────────────────────────────


class TestRedeemExpired:
    def test_expired_coupon_returns_expired_status(self, svc: CouponService) -> None:
        coupon = _issue(svc)
        # expires_at을 과거로 조작
        data = json.loads(Path(svc._path).read_text(encoding="utf-8"))
        for c in data["coupons"]:
            if c["code"] == coupon["code"]:
                c["expires_at"] = (
                    datetime.now(timezone.utc) - timedelta(days=1)
                ).isoformat()
        Path(svc._path).write_text(json.dumps(data), encoding="utf-8")

        result = svc.redeem_coupon(coupon["code"], "POS-1")
        assert result["redeem_status"] == "expired"
        assert result["coupon"]["status"] == "expired"

    def test_expired_status_persisted(self, svc: CouponService) -> None:
        coupon = _issue(svc)
        data = json.loads(Path(svc._path).read_text(encoding="utf-8"))
        for c in data["coupons"]:
            if c["code"] == coupon["code"]:
                c["expires_at"] = (
                    datetime.now(timezone.utc) - timedelta(days=1)
                ).isoformat()
        Path(svc._path).write_text(json.dumps(data), encoding="utf-8")

        svc.redeem_coupon(coupon["code"], "POS-1")
        reloaded = json.loads(Path(svc._path).read_text(encoding="utf-8"))
        status = next(
            c["status"] for c in reloaded["coupons"] if c["code"] == coupon["code"]
        )
        assert status == "expired"


# ── generate_coupon_code ─────────────────────────────────────────────────────


class TestGenerateCouponCode:
    def test_length_matches_constant(self) -> None:
        from app.core.config import constants

        code = CouponService.generate_coupon_code()
        assert len(code) == constants.COUPON_CODE_LENGTH

    def test_only_uppercase_and_digits(self) -> None:
        import string

        code = CouponService.generate_coupon_code()
        allowed = set(string.ascii_uppercase + string.digits)
        assert all(c in allowed for c in code)

    def test_codes_are_random(self) -> None:
        codes = {CouponService.generate_coupon_code() for _ in range(20)}
        assert len(codes) > 1
