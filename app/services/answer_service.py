import json
import os
import random
from datetime import date

from app.core.config import settings

ANSWER_FILE = os.path.join(settings.DATA_DIR, "answer.json")
STATE_FILE = os.path.join(settings.DATA_DIR, "current_answer.json")


def load_missions1():
    """missions1(장소 찾기) 리스트를 로드한다."""
    with open(ANSWER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("missions1", [])


def load_missions2():
    """missions2(감성 촬영) 리스트를 로드한다."""
    with open(ANSWER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("missions2", [])


def get_today_answers(admin_choice1=None, admin_choice2=None):
    """오늘의 정답과 힌트를 반환한다. 이미 오늘 생성된 정답이 있으면 캐시에서 반환.

    Args:
        admin_choice1: 관리자가 지정한 미션1 정답 (선택)
        admin_choice2: 관리자가 지정한 미션2 정답 (선택)

    Returns:
        (answer1, answer2, hint1, hint2) 튜플
    """
    today = str(date.today())
    os.makedirs(settings.DATA_DIR, exist_ok=True)

    # 캐시된 오늘 정답이 있으면 반환
    if not admin_choice1 and not admin_choice2:
        if os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 0:
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        state = json.loads(content)
                        if state.get("date") == today:
                            return (
                                state.get("answer1"),
                                state.get("answer2"),
                                state.get("hint1"),
                                state.get("hint2"),
                            )
            except Exception as e:
                print(f"⚠️ 상태 파일 읽기 오류: {e}. 새로 생성합니다.")

    # 미션1 정답 결정
    missions1_candidates = load_missions1()
    if admin_choice1:
        match = next(
            (m for m in missions1_candidates if m["answer"] == admin_choice1), None
        )
        if not match:
            raise ValueError(f"잘못된 미션1 선택: {admin_choice1}")
        answer1, hint1 = match["answer"], match["hint"]
    else:
        choice = random.choice(missions1_candidates)
        answer1, hint1 = choice["answer"], choice["hint"]

    # 미션2 정답 결정
    missions2_candidates = load_missions2()
    if admin_choice2:
        match = next(
            (m for m in missions2_candidates if m["answer"] == admin_choice2), None
        )
        if not match:
            raise ValueError(f"잘못된 미션2 선택: {admin_choice2}")
        answer2, hint2 = match["answer"], match["hint"]
    else:
        choice = random.choice(missions2_candidates)
        answer2, hint2 = choice["answer"], choice["hint"]

    # 상태 파일에 저장
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
