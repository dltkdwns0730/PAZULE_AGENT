"""Coupon issuance and redeem service with file-based persistence."""

from __future__ import annotations

import json
import os
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import constants, settings


class CouponService:
    """파일 기반 JSON 스토리지를 이용한 쿠폰 발급·조회·사용 서비스."""

    def __init__(self) -> None:
        """쿠폰 저장 경로를 초기화하고 data 디렉터리를 생성한다."""
        self._path = os.path.join(settings.DATA_DIR, "coupons.json")
        os.makedirs(settings.DATA_DIR, exist_ok=True)

    def _read_all(self) -> dict[str, Any]:
        """쿠폰 JSON 파일 전체를 읽어 반환한다.

        Returns:
            쿠폰 목록을 담은 딕셔너리. 파일이 없거나 오류 시 {"coupons": []}.
        """
        if not os.path.exists(self._path):
            return {"coupons": []}
        try:
            with open(self._path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {"coupons": []}

    def _write_all(self, payload: dict[str, Any]) -> None:
        """쿠폰 데이터를 JSON 파일에 덮어쓴다.

        Args:
            payload: 저장할 쿠폰 데이터 딕셔너리.
        """
        with open(self._path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    @staticmethod
    def generate_coupon_code() -> str:
        """COUPON_CODE_LENGTH 자리 영대문자+숫자 쿠폰 코드를 생성한다.

        Returns:
            예: 'A3KX9PTM'
        """
        return "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=constants.COUPON_CODE_LENGTH,
            )
        )

    def _find_by_code(self, code: str) -> dict[str, Any] | None:
        """코드로 쿠폰을 조회한다.

        Args:
            code: 조회할 쿠폰 코드.

        Returns:
            일치하는 쿠폰 딕셔너리, 없으면 None.
        """
        data = self._read_all()
        for coupon in data.get("coupons", []):
            if coupon.get("code") == code:
                return coupon
        return None

    def _find_by_mission_id(self, mission_id: str) -> dict[str, Any] | None:
        """미션 ID로 기발급 쿠폰을 조회한다.

        Args:
            mission_id: 조회할 미션 세션 ID.

        Returns:
            일치하는 쿠폰 딕셔너리, 없으면 None.
        """
        data = self._read_all()
        for coupon in data.get("coupons", []):
            if coupon.get("mission_id") == mission_id:
                return coupon
        return None

    def _find_by_user_and_answer(
        self, user_id: str, answer: str
    ) -> dict[str, Any] | None:
        """사용자 ID와 정답 키워드로 발급된 쿠폰을 조회한다.

        Args:
            user_id: 사용자 식별자.
            answer: 미션 정답 키워드.

        Returns:
            일치하는 쿠폰 딕셔너리, 없으면 None.
        """
        data = self._read_all()
        for coupon in data.get("coupons", []):
            if coupon.get("user_id") == user_id and coupon.get("answer") == answer:
                return coupon
        return None

    def has_coupon_for_answer(self, user_id: str, answer: str) -> bool:
        """사용자가 특정 정답에 대한 쿠폰을 이미 보유하고 있는지 확인한다.

        Args:
            user_id: 사용자 식별자.
            answer: 미션 정답 키워드.

        Returns:
            보유 중이면 True, 아니면 False.
        """
        return self._find_by_user_and_answer(user_id, answer) is not None

    def issue_coupon(
        self,
        mission_type: str,
        answer: str,
        mission_id: str | None = None,
        user_id: str = "guest",
        partner_id: str | None = None,
        discount_rule: str = constants.DEFAULT_DISCOUNT_RULE,
    ) -> dict[str, Any]:
        """쿠폰을 발급하고 저장한다. 멱등성을 보장하며 중복 발급을 방지한다.

        Args:
            mission_type: 'mission1'(위치) 또는 'mission2'(분위기).
            answer: 미션 정답 키워드.
            mission_id: 미션 세션 ID (멱등성 키).
            user_id: 사용자 식별자.
            partner_id: 파트너 식별자.
            discount_rule: 할인 규칙 문자열 (기본값: DEFAULT_DISCOUNT_RULE).

        Returns:
            발급된 쿠폰 딕셔너리.
        """
        # 1. 미션 ID 기반 멱등성 체크 (동일 세션 재요청)
        if mission_id:
            existing_by_session = self._find_by_mission_id(mission_id)
            if existing_by_session:
                return existing_by_session

        # 2. 사용자 + 정답 기반 중복 체크 (다른 세션이지만 동일 미션 성공)
        existing_by_user = self._find_by_user_and_answer(user_id, answer)
        if existing_by_user:
            return existing_by_user

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
            "user_id": user_id,
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

    def redeem_coupon(self, code: str, partner_pos_id: str) -> dict[str, Any]:
        """쿠폰을 사용 처리한다. 만료·중복·미존재 케이스를 구분해 반환한다.

        Args:
            code: 사용할 쿠폰 코드.
            partner_pos_id: POS 단말 식별자.

        Returns:
            {redeem_status, message, coupon(선택)} 딕셔너리.
            redeem_status: 'redeemed' | 'already_redeemed' | 'expired' | 'not_found'.
        """
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

    def get_user_coupons(self, user_id: str) -> list[dict[str, Any]]:
        """사용자가 보유한 모든 쿠폰 목록을 조회한다.

        Args:
            user_id: 사용자 식별자.

        Returns:
            쿠폰 딕셔너리 리스트.
        """
        data = self._read_all()
        # 쿠폰 객체에 저장된 user_id를 직접 확인 (새로운 방식)
        # 또는 mission_id를 통해 세션 데이터와 대조 (기존 방식 보완)
        user_coupons = [
            c for c in data.get("coupons", []) if c.get("user_id") == user_id
        ]

        # 하위 호환성을 위해: user_id가 없는 예전 쿠폰들은 세션 데이터를 통해 한 번 더 확인
        if user_id == "guest":
            from app.services.mission_session_service import mission_session_service

            session_data = mission_session_service._read_all()
            user_mission_ids = {
                s.get("mission_id")
                for s in session_data.get("sessions", [])
                if s.get("user_id") == user_id
            }

            existing_ids = {c.get("mission_id") for c in user_coupons}
            old_coupons = [
                c
                for c in data.get("coupons", [])
                if c.get("mission_id") in user_mission_ids
                and c.get("mission_id") not in existing_ids
            ]
            user_coupons.extend(old_coupons)

        return user_coupons


coupon_service = CouponService()
