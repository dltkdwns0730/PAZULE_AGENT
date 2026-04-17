"""정답 서비스 모듈: 오늘의 미션 정답을 로드하고 캐싱한다."""

from __future__ import annotations

import json
import logging
import os
import random
from datetime import date

from app.core.config import settings

logger = logging.getLogger(__name__)

ANSWER_FILE = os.path.join(settings.DATA_DIR, "answer.json")
STATE_FILE = os.path.join(settings.DATA_DIR, "current_answer.json")


def load_missions1() -> list[dict[str, str]]:
    """missions1(장소 찾기) 리스트를 로드한다.

    Returns:
        장소 찾기 미션 목록.
    """
    with open(ANSWER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("missions1", [])


def load_missions2() -> list[dict[str, str]]:
    """missions2(감성 촬영) 리스트를 로드한다.

    Returns:
        감성 촬영 미션 목록.
    """
    with open(ANSWER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("missions2", [])


def _load_cached_answers(today: str) -> tuple[str, str, str, str] | None:
    """오늘 날짜의 캐시된 정답을 반환한다.

    Args:
        today: 오늘 날짜 문자열 (YYYY-MM-DD).

    Returns:
        (answer1, answer2, hint1, hint2) 튜플 또는 캐시 미스 시 None.
    """
    if not (os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 0):
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return None
        state = json.loads(content)
        if state.get("date") == today:
            return (
                state.get("answer1"),
                state.get("answer2"),
                state.get("hint1"),
                state.get("hint2"),
            )
    except Exception as exc:
        logger.warning("상태 파일 읽기 오류: %s. 새로 생성합니다.", exc)
    return None


def _resolve_mission1(admin_choice1: str | None) -> tuple[str, str]:
    """미션1 정답과 힌트를 결정한다.

    Args:
        admin_choice1: 관리자가 지정한 미션1 정답 (선택).

    Returns:
        (answer1, hint1) 튜플.

    Raises:
        ValueError: 지정한 정답이 목록에 없는 경우.
    """
    candidates = load_missions1()
    if admin_choice1:
        match = next((m for m in candidates if m["answer"] == admin_choice1), None)
        if not match:
            raise ValueError(f"잘못된 미션1 선택: {admin_choice1}")
        return match["answer"], match["hint"]
    choice = random.choice(candidates)
    return choice["answer"], choice["hint"]


def _resolve_mission2(admin_choice2: str | None) -> tuple[str, str]:
    """미션2 정답과 힌트를 결정한다.

    Args:
        admin_choice2: 관리자가 지정한 미션2 정답 (선택).

    Returns:
        (answer2, hint2) 튜플.

    Raises:
        ValueError: 지정한 정답이 목록에 없는 경우.
    """
    candidates = load_missions2()
    if admin_choice2:
        match = next((m for m in candidates if m["answer"] == admin_choice2), None)
        if not match:
            raise ValueError(f"잘못된 미션2 선택: {admin_choice2}")
        return match["answer"], match["hint"]
    choice = random.choice(candidates)
    return choice["answer"], choice["hint"]


def get_today_answers(
    admin_choice1: str | None = None, admin_choice2: str | None = None
) -> tuple[str, str, str, str]:
    """오늘의 정답과 힌트를 반환한다. 이미 오늘 생성된 정답이 있으면 캐시에서 반환.

    Args:
        admin_choice1: 관리자가 지정한 미션1 정답 (선택).
        admin_choice2: 관리자가 지정한 미션2 정답 (선택).

    Returns:
        (answer1, answer2, hint1, hint2) 튜플.
    """
    today = str(date.today())
    os.makedirs(settings.DATA_DIR, exist_ok=True)

    if not admin_choice1 and not admin_choice2:
        cached = _load_cached_answers(today)
        if cached is not None:
            return cached

    answer1, hint1 = _resolve_mission1(admin_choice1)
    answer2, hint2 = _resolve_mission2(admin_choice2)

    state = {
        "date": today,
        "answer1": answer1,
        "answer2": answer2,
        "hint1": hint1,
        "hint2": hint2,
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return answer1, answer2, hint1, hint2
