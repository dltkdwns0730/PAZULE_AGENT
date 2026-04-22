"""answer_service 단위 테스트.

공공 환경 호환 설계:
  - 실제 파일 I/O → tmp_path pytest fixture로 격리
  - settings.DATA_DIR → tmp_path로 패치
  - ANSWER_FILE·STATE_FILE → tmp_path 기반 경로로 패치
  - 외부 의존성 없음 (순수 파일 I/O 서비스)

검증 대상:
  - load_missions1 / load_missions2: 파일 파싱
  - _load_cached_answers: 날짜 일치 캐시 히트, 날짜 불일치 캐시 미스, 파일 없음
  - _resolve_mission1 / _resolve_mission2: 관리자 선택, 랜덤 선택, 잘못된 선택 오류
  - get_today_answers: 캐시 히트 경로, 캐시 미스 → 파일 생성, 관리자 선택 캐시 우회
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest


# ── fixture ─────────────────────────────────────────────────────────────────

MISSIONS1 = [
    {"answer": "gangnam_station", "hint": "역 출구"},
    {"answer": "coex", "hint": "수족관"},
    {"answer": "n_tower", "hint": "야경"},
]

MISSIONS2 = [
    {"answer": "sunset", "hint": "붉은 하늘"},
    {"answer": "rain_bokeh", "hint": "빗방울"},
]

ANSWER_JSON = {"missions1": MISSIONS1, "missions2": MISSIONS2}


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    """테스트용 임시 DATA_DIR."""
    return tmp_path / "data"


@pytest.fixture()
def answer_file(data_dir: Path) -> Path:
    """ANSWER_FILE — 미션 목록 JSON."""
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "answer.json"
    path.write_text(json.dumps(ANSWER_JSON, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture()
def state_file(data_dir: Path) -> Path:
    """STATE_FILE 경로 (아직 파일 없음 상태)."""
    return data_dir / "current_answer.json"


def _patch_files(answer_file: Path, state_file: Path):
    """ANSWER_FILE·STATE_FILE 모듈 변수를 tmp_path 기반 경로로 교체."""
    return (
        patch("app.services.answer_service.ANSWER_FILE", str(answer_file)),
        patch("app.services.answer_service.STATE_FILE", str(state_file)),
    )


# ── load_missions1 ───────────────────────────────────────────────────────────


class TestLoadMissions1:
    def test_returns_list(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions1

            result = load_missions1()
        assert isinstance(result, list)

    def test_count_matches_fixture(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions1

            result = load_missions1()
        assert len(result) == len(MISSIONS1)

    def test_contains_answer_key(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions1

            result = load_missions1()
        assert all("answer" in m for m in result)

    def test_contains_hint_key(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions1

            result = load_missions1()
        assert all("hint" in m for m in result)


# ── load_missions2 ───────────────────────────────────────────────────────────


class TestLoadMissions2:
    def test_returns_correct_count(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions2

            result = load_missions2()
        assert len(result) == len(MISSIONS2)

    def test_values_match_fixture(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions2

            result = load_missions2()
        answers = {m["answer"] for m in result}
        assert answers == {"sunset", "rain_bokeh"}


# ── _load_cached_answers ─────────────────────────────────────────────────────


class TestLoadCachedAnswers:
    def test_no_state_file_returns_none(self, answer_file, state_file) -> None:
        """STATE_FILE이 없으면 None 반환."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _load_cached_answers

            result = _load_cached_answers("2026-04-18")
        assert result is None

    def test_today_match_returns_tuple(self, answer_file, state_file) -> None:
        today = "2026-04-18"
        cache = {
            "date": today,
            "answer1": "gangnam_station",
            "answer2": "sunset",
            "hint1": "역 출구",
            "hint2": "붉은 하늘",
        }
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(cache), encoding="utf-8")

        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _load_cached_answers

            result = _load_cached_answers(today)
        assert result == ("gangnam_station", "sunset", "역 출구", "붉은 하늘")

    def test_date_mismatch_returns_none(self, answer_file, state_file) -> None:
        cache = {
            "date": "2026-01-01",
            "answer1": "x",
            "answer2": "y",
            "hint1": "h1",
            "hint2": "h2",
        }
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(cache), encoding="utf-8")

        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _load_cached_answers

            result = _load_cached_answers("2026-04-18")
        assert result is None

    def test_empty_state_file_returns_none(self, answer_file, state_file) -> None:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("", encoding="utf-8")

        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _load_cached_answers

            result = _load_cached_answers("2026-04-18")
        assert result is None

    def test_corrupted_json_returns_none(self, answer_file, state_file) -> None:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("{corrupted json}", encoding="utf-8")

        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _load_cached_answers

            result = _load_cached_answers("2026-04-18")
        assert result is None


# ── _resolve_mission1 ────────────────────────────────────────────────────────


class TestResolveMission1:
    def test_admin_choice_returns_exact_match(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _resolve_mission1

            answer, hint = _resolve_mission1("coex")
        assert answer == "coex"
        assert hint == "수족관"

    def test_invalid_admin_choice_raises(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _resolve_mission1

            with pytest.raises(ValueError, match="잘못된 미션1"):
                _resolve_mission1("nonexistent_place")

    def test_none_choice_returns_random(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        valid_answers = {m["answer"] for m in MISSIONS1}
        with p1, p2:
            from app.services.answer_service import _resolve_mission1

            answer, hint = _resolve_mission1(None)
        assert answer in valid_answers

    def test_empty_string_choice_returns_random(self, answer_file, state_file) -> None:
        """빈 문자열은 관리자 선택 없음 → 랜덤."""
        p1, p2 = _patch_files(answer_file, state_file)
        valid_answers = {m["answer"] for m in MISSIONS1}
        with p1, p2:
            from app.services.answer_service import _resolve_mission1

            answer, _ = _resolve_mission1("")
        assert answer in valid_answers


# ── _resolve_mission2 ────────────────────────────────────────────────────────


class TestResolveMission2:
    def test_admin_choice_returns_exact_match(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _resolve_mission2

            answer, hint = _resolve_mission2("rain_bokeh")
        assert answer == "rain_bokeh"
        assert hint == "빗방울"

    def test_invalid_admin_choice_raises(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _resolve_mission2

            with pytest.raises(ValueError, match="잘못된 미션2"):
                _resolve_mission2("invalid_theme")

    def test_none_returns_random_from_pool(self, answer_file, state_file) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        valid_answers = {m["answer"] for m in MISSIONS2}
        with p1, p2:
            from app.services.answer_service import _resolve_mission2

            answer, _ = _resolve_mission2(None)
        assert answer in valid_answers


# ── get_today_answers ────────────────────────────────────────────────────────


class TestGetTodayAnswers:
    def test_cache_miss_writes_state_file(
        self, answer_file, state_file, data_dir
    ) -> None:
        """캐시 없을 때 실행 후 STATE_FILE이 생성됨."""
        p1, p2 = _patch_files(answer_file, state_file)
        with (
            p1,
            p2,
            patch("app.services.answer_service.settings") as mock_settings,
        ):
            mock_settings.DATA_DIR = str(data_dir)
            from app.services.answer_service import get_today_answers

            get_today_answers()
        assert state_file.exists()

    def test_cache_miss_returns_four_tuple(
        self, answer_file, state_file, data_dir
    ) -> None:
        p1, p2 = _patch_files(answer_file, state_file)
        with (
            p1,
            p2,
            patch("app.services.answer_service.settings") as mock_settings,
        ):
            mock_settings.DATA_DIR = str(data_dir)
            from app.services.answer_service import get_today_answers

            result = get_today_answers()
        assert len(result) == 4

    def test_cache_hit_returns_cached_values(
        self, answer_file, state_file, data_dir
    ) -> None:
        """오늘 날짜 캐시가 있으면 STATE_FILE에서 반환."""
        today = str(date.today())
        cache = {
            "date": today,
            "answer1": "n_tower",
            "answer2": "sunset",
            "hint1": "야경",
            "hint2": "붉은 하늘",
        }
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(cache), encoding="utf-8")

        p1, p2 = _patch_files(answer_file, state_file)
        with (
            p1,
            p2,
            patch("app.services.answer_service.settings") as mock_settings,
        ):
            mock_settings.DATA_DIR = str(data_dir)
            from app.services.answer_service import get_today_answers

            result = get_today_answers()
        assert result == ("n_tower", "sunset", "야경", "붉은 하늘")

    def test_admin_choice_bypasses_cache(
        self, answer_file, state_file, data_dir
    ) -> None:
        """관리자 선택이 있으면 캐시를 우회하고 지정 정답 반환."""
        today = str(date.today())
        # 캐시에 다른 값을 저장해 둠
        cache = {
            "date": today,
            "answer1": "coex",
            "answer2": "rain_bokeh",
            "hint1": "수족관",
            "hint2": "빗방울",
        }
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(cache), encoding="utf-8")

        p1, p2 = _patch_files(answer_file, state_file)
        with (
            p1,
            p2,
            patch("app.services.answer_service.settings") as mock_settings,
        ):
            mock_settings.DATA_DIR = str(data_dir)
            from app.services.answer_service import get_today_answers

            answer1, _, _, _ = get_today_answers(admin_choice1="gangnam_station")
        assert answer1 == "gangnam_station"  # 캐시 값 coex가 아닌 지정값

    def test_written_state_matches_returned_values(
        self, answer_file, state_file, data_dir
    ) -> None:
        """쓰인 STATE_FILE 내용과 반환값이 일치."""
        p1, p2 = _patch_files(answer_file, state_file)
        with (
            p1,
            p2,
            patch("app.services.answer_service.settings") as mock_settings,
        ):
            mock_settings.DATA_DIR = str(data_dir)
            from app.services.answer_service import get_today_answers

            a1, a2, h1, h2 = get_today_answers()

        written = json.loads(state_file.read_text(encoding="utf-8"))
        assert written["answer1"] == a1
        assert written["answer2"] == a2
        assert written["hint1"] == h1
        assert written["hint2"] == h2
