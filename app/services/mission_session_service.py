"""Mission session persistence and policy checks."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.core.config import settings
from app.core.utils import normalize_mission_type


def _utcnow() -> datetime:
    """현재 UTC 시각을 반환한다."""
    return datetime.now(timezone.utc)


class MissionSessionService:
    """파일 기반 JSON 스토리지를 이용한 미션 세션 생성·조회·갱신 서비스."""

    def __init__(self) -> None:
        """세션 저장 경로를 초기화하고 data 디렉터리를 생성한다."""
        self._path = os.path.join(settings.DATA_DIR, "mission_sessions.json")
        os.makedirs(settings.DATA_DIR, exist_ok=True)

    def _read_all(self) -> dict[str, Any]:
        """세션 JSON 파일 전체를 읽어 반환한다.

        Returns:
            세션 목록을 담은 딕셔너리. 파일이 없거나 오류 시 {"sessions": []}.
        """
        if not os.path.exists(self._path):
            return {"sessions": []}
        try:
            with open(self._path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {"sessions": []}

    def _write_all(self, payload: dict[str, Any]) -> None:
        """세션 데이터를 JSON 파일에 덮어쓴다.

        Args:
            payload: 저장할 세션 데이터 딕셔너리.
        """
        with open(self._path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    def create_session(
        self,
        user_id: str,
        site_id: str,
        mission_type: str,
        answer: str,
        hint: str,
    ) -> dict[str, Any]:
        """새 미션 세션을 생성하고 저장한다.

        Args:
            user_id: 사용자 식별자.
            site_id: 사이트 식별자.
            mission_type: 'location' | 'atmosphere'.
            answer: 오늘의 미션 정답.
            hint: 미션 힌트 문자열.

        Returns:
            생성된 세션 딕셔너리.
        """
        now = _utcnow()
        expires = now + timedelta(minutes=settings.MISSION_SESSION_TTL_MINUTES)
        session = {
            "mission_id": str(uuid.uuid4()),
            "user_id": user_id or "guest",
            "site_id": site_id or "pazule-default",
            "mission_type": normalize_mission_type(mission_type),
            "answer": answer,
            "hint": hint,
            "status": "created",
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "max_submissions": settings.MISSION_MAX_SUBMISSIONS,
            "submissions": [],
            "latest_judgment": None,
        }
        data = self._read_all()
        data.setdefault("sessions", []).append(session)
        self._write_all(data)
        return session

    def get_session(self, mission_id: str) -> dict[str, Any] | None:
        """mission_id로 세션을 조회한다.

        Args:
            mission_id: 조회할 미션 세션 ID.

        Returns:
            일치하는 세션 딕셔너리, 없으면 None.
        """
        data = self._read_all()
        for session in data.get("sessions", []):
            if session.get("mission_id") == mission_id:
                return session
        return None

    def _update_session(
        self,
        mission_id: str,
        mutate_fn: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> dict[str, Any] | None:
        """세션을 읽어 mutate_fn으로 변경한 뒤 저장한다.

        Args:
            mission_id: 갱신할 미션 세션 ID.
            mutate_fn: 세션 딕셔너리를 받아 수정된 딕셔너리를 반환하는 함수.

        Returns:
            갱신된 세션 딕셔너리, 세션이 없으면 None.
        """
        data = self._read_all()
        updated = None
        for idx, session in enumerate(data.get("sessions", [])):
            if session.get("mission_id") == mission_id:
                updated = mutate_fn(dict(session))
                data["sessions"][idx] = updated
                break
        if updated is None:
            return None
        self._write_all(data)
        return updated

    def can_submit(self, mission_id: str) -> tuple[bool, str]:
        """미션 제출 가능 여부를 검사한다.

        Args:
            mission_id: 검사할 미션 세션 ID.

        Returns:
            (True, 'ok') 가능, (False, reason) 불가.
            reason: 'session_not_found' | 'session_expired' | 'submission_limit_reached'.
        """
        session = self.get_session(mission_id)
        if not session:
            return False, "session_not_found"
        if _utcnow() > datetime.fromisoformat(session["expires_at"]):
            return False, "session_expired"
        if len(session.get("submissions", [])) >= int(
            session.get("max_submissions", 0)
        ):
            return False, "submission_limit_reached"
        return True, "ok"

    def record_submission(
        self,
        mission_id: str,
        image_hash: str,
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """제출 기록과 최신 판정 결과를 세션에 저장한다.

        Args:
            mission_id: 미션 세션 ID.
            image_hash: 제출 이미지의 SHA-256 해시.
            result: AI 판정 결과 딕셔너리.

        Returns:
            갱신된 세션 딕셔너리, 세션이 없으면 None.
        """

        def mutate(session: dict[str, Any]) -> dict[str, Any]:
            session["status"] = "submitted"
            session.setdefault("submissions", []).append(
                {
                    "submitted_at": _utcnow().isoformat(),
                    "image_hash": image_hash,
                    "result_summary": {
                        "success": bool(result.get("success")),
                        "confidence": result.get("confidence"),
                    },
                }
            )
            session["latest_judgment"] = result
            return session

        return self._update_session(mission_id, mutate)

    def mark_coupon_issued(
        self, mission_id: str, coupon_code: str
    ) -> dict[str, Any] | None:
        """쿠폰 발급 완료 상태를 세션에 기록한다.

        Args:
            mission_id: 미션 세션 ID.
            coupon_code: 발급된 쿠폰 코드.

        Returns:
            갱신된 세션 딕셔너리, 세션이 없으면 None.
        """

        def mutate(session: dict[str, Any]) -> dict[str, Any]:
            session["coupon_code"] = coupon_code
            session["status"] = "coupon_issued"
            return session

        return self._update_session(mission_id, mutate)

    def is_duplicate_hash_for_user(self, user_id: str, image_hash: str) -> bool:
        """동일 사용자의 이전 제출 중 같은 이미지 해시가 있는지 검사한다.

        Args:
            user_id: 사용자 식별자.
            image_hash: 검사할 이미지 SHA-256 해시.

        Returns:
            중복이면 True, 아니면 False.
        """
        if not image_hash:
            return False
        data = self._read_all()
        for session in data.get("sessions", []):
            if session.get("user_id") != user_id:
                continue
            for sub in session.get("submissions", []):
                if sub.get("image_hash") == image_hash:
                    return True
        return False

    @staticmethod
    def hash_file(file_path: str) -> str:
        """파일을 SHA-256으로 해시하여 16진수 문자열을 반환한다.

        Args:
            file_path: 해시할 파일의 절대 경로.

        Returns:
            SHA-256 hex digest 문자열.
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


mission_session_service = MissionSessionService()
