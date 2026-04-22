import json
import pytest
from unittest.mock import patch
from app.services.answer_service import get_today_answers, load_mission_location


@pytest.fixture
def mock_answer_json(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    answer_file = data_dir / "answer.json"

    mock_data = {
        "mission-location": [
            {"answer": "loc1", "hint": "hint_loc1", "vqa_hints": ["v1"]},
            {"answer": "loc2", "hint": "hint_loc2", "vqa_hints": ["v2"]},
        ],
        "mission-atmosphere": [
            {"answer": "atm1", "hint": "hint_atm1", "vqa_hints": ["v3"]},
            {"answer": "atm2", "hint": "hint_atm2", "vqa_hints": ["v4"]},
        ],
    }
    answer_file.write_text(json.dumps(mock_data, ensure_ascii=False), encoding="utf-8")

    # settings.DATA_DIR를 tmp_path로 오버라이드
    from app.core.config import settings

    monkeypatch.setattr(settings, "DATA_DIR", str(data_dir))

    # answer_service 모듈 내의 전역 변수들 업데이트 필요
    import app.services.answer_service

    monkeypatch.setattr(app.services.answer_service, "ANSWER_FILE", str(answer_file))
    monkeypatch.setattr(
        app.services.answer_service, "STATE_FILE", str(data_dir / "current_answer.json")
    )

    return answer_file


def test_load_mission_location(mock_answer_json):
    locs = load_mission_location()
    assert len(locs) == 2
    assert locs[0]["answer"] == "loc1"


def test_get_today_answers_random(mock_answer_json):
    # 첫 호출: 랜덤 생성 및 캐싱
    ans1, ans2, h1, h2, v1, v2 = get_today_answers()
    assert ans1 in ["loc1", "loc2"]
    assert ans2 in ["atm1", "atm2"]

    # 두 번째 호출: 캐시된 결과 반환 확인
    with patch("random.choice") as mock_choice:
        ans1_2, ans2_2, h1_2, h2_2, v1_2, v2_2 = get_today_answers()
        assert ans1 == ans1_2
        assert mock_choice.call_count == 0


def test_get_today_answers_admin_choice(mock_answer_json):
    ans1, ans2, h1, h2, v1, v2 = get_today_answers(
        admin_choice1="loc2", admin_choice2="atm1"
    )
    assert ans1 == "loc2"
    assert ans2 == "atm1"
    assert h1 == "hint_loc2"
    assert v1 == ["v2"]


def test_get_today_answers_invalid_admin_choice(mock_answer_json):
    with pytest.raises(ValueError, match="잘못된 location 미션 선택"):
        get_today_answers(admin_choice1="wrong_loc")


def test_cache_reloads_on_new_day(mock_answer_json, monkeypatch):
    # 1. 오늘 날짜로 캐시 생성
    get_today_answers()

    # 2. 상태 파일의 날짜를 과거로 강제 변경하여 캐시 미스 유도
    import app.services.answer_service

    state_file = app.services.answer_service.STATE_FILE
    with open(state_file, "r", encoding="utf-8") as f:
        state = json.load(f)
    state["date"] = "2000-01-01"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f)

    # 3. 호출 시 캐시 미스가 발생하여 random.choice가 호출되어야 함
    with patch("app.services.answer_service.random.choice") as mock_choice:
        mock_choice.side_effect = [
            {"answer": "loc1", "hint": "h", "vqa_hints": []},
            {"answer": "atm1", "hint": "h", "vqa_hints": []},
        ]

        ans = get_today_answers()
        assert ans[0] == "loc1"
        assert mock_choice.call_count == 2
