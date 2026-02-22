"""Coupon issuance and redeem service with file-based persistence."""

from __future__ import annotations

import json
import os
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.core.config import settings


class CouponService:
    """Purpose: `CouponService` ??? ??? ?? ??? ???
    Context: ?? ???? ?? ??? ??? ??
    Attrs: ?? ?? ???? ?? ??? ???"""
    def __init__(self):
        """Caller: ?? ?? ???? ???
        Purpose: `__init__` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: None
        Note: ?? ?? ?? ???? ???"""
        self._path = os.path.join(settings.DATA_DIR, "coupons.json")
        os.makedirs(settings.DATA_DIR, exist_ok=True)

    def _read_all(self) -> Dict[str, Any]:
        """Caller: ?? ?? ???? ???
        Purpose: `_read_all` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: None
        Note: ?? ?? ?? ???? ???"""
        if not os.path.exists(self._path):
            return {"coupons": []}
        try:
            with open(self._path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {"coupons": []}

    def _write_all(self, payload: Dict[str, Any]) -> None:
        """Caller: ?? ?? ???? ???
        Purpose: `_write_all` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: payload: ???? ???? ??
        Note: ?? ?? ?? ???? ???"""
        with open(self._path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    @staticmethod
    def generate_coupon_code() -> str:
        """Caller: ?? ?? ???? ???
        Purpose: `generate_coupon_code` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: None
        Note: ?? ?? ?? ???? ???"""
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def _find_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Caller: ?? ?? ???? ???
        Purpose: `_find_by_code` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: code: ???? ???? ??
        Note: ?? ?? ?? ???? ???"""
        data = self._read_all()
        for coupon in data.get("coupons", []):
            if coupon.get("code") == code:
                return coupon
        return None

    def _find_by_mission_id(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Caller: ?? ?? ???? ???
        Purpose: `_find_by_mission_id` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: mission_id: ???? ???? ??
        Note: ?? ?? ?? ???? ???"""
        data = self._read_all()
        for coupon in data.get("coupons", []):
            if coupon.get("mission_id") == mission_id:
                return coupon
        return None

    def issue_coupon(
        self,
        mission_type: str,
        answer: str,
        mission_id: Optional[str] = None,
        partner_id: Optional[str] = None,
        discount_rule: str = "10%_OFF",
    ) -> Dict[str, Any]:
        # Idempotent path for mission-based issuance.
        """Caller: ?? ?? ???? ???
        Purpose: `issue_coupon` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: mission_type: ???? ???? ??; answer: ???? ???? ??; mission_id: ???? ???? ??; partner_id: ???? ???? ??; discount_rule: ???? ???? ??
        Note: ?? ?? ?? ???? ???"""
        if mission_id:
            existing = self._find_by_mission_id(mission_id)
            if existing:
                return existing

        code = self.generate_coupon_code()
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + timedelta(days=7)
        description = (
            f"{answer} 장소 미션 완료 쿠폰"
            if mission_type == "mission1"
            else f"{answer} 분위기 미션 완료 쿠폰"
        )

        coupon = {
            "code": code,
            "description": description,
            "mission_type": mission_type,
            "answer": answer,
            "mission_id": mission_id,
            "partner_id": partner_id,
            "discount_rule": discount_rule,
            "status": "issued",
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "redeemed_at": None,
            "partner_pos_id": None,
        }

        data = self._read_all()
        data.setdefault("coupons", []).append(coupon)
        self._write_all(data)
        return coupon

    def redeem_coupon(self, code: str, partner_pos_id: str) -> Dict[str, Any]:
        """Caller: ?? ?? ???? ???
        Purpose: `redeem_coupon` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: code: ???? ???? ??; partner_pos_id: ???? ???? ??
        Note: ?? ?? ?? ???? ???"""
        data = self._read_all()
        target_idx = None
        target = None
        for idx, coupon in enumerate(data.get("coupons", [])):
            if coupon.get("code") == code:
                target_idx = idx
                target = dict(coupon)
                break

        if not target:
            return {"redeem_status": "not_found", "message": "Coupon not found."}

        if target.get("status") == "redeemed":
            return {
                "redeem_status": "already_redeemed",
                "message": "Coupon already redeemed.",
                "coupon": target,
            }

        if datetime.now(timezone.utc) > datetime.fromisoformat(target["expires_at"]):
            target["status"] = "expired"
            data["coupons"][target_idx] = target
            self._write_all(data)
            return {
                "redeem_status": "expired",
                "message": "Coupon expired.",
                "coupon": target,
            }

        target["status"] = "redeemed"
        target["redeemed_at"] = datetime.now(timezone.utc).isoformat()
        target["partner_pos_id"] = partner_pos_id
        data["coupons"][target_idx] = target
        self._write_all(data)
        return {
            "redeem_status": "redeemed",
            "message": "Coupon redeemed.",
            "coupon": target,
        }


coupon_service = CouponService()
