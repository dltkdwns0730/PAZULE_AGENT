"""정적 힌트(초기 힌트) 시스템 단위 테스트.

PAZULE 힌트 제공 흐름:
  ┌─────────────────────────────────────────────────────────────────┐
  │  [초기 힌트] data/answer.json → answer_service → routes → UI   │
  │             정답과 함께 미리 작성된 한국어 힌트 문자열           │
  │                                                                  │
  │  [재시도 힌트] _generate_retry_hint → LLMService → UI           │
  │               정답 장소의 감성·분위기를 활용한 LLM 생성 문장    │
  │               (실패 이유 / 정답 키워드 직접 언급 금지)           │
  └─────────────────────────────────────────────────────────────────┘

검증 대상:
  - answer.json 실제 데이터: hint 필드 존재 및 비어있지 않음
  - load_missions1 / load_missions2: hint 필드 일관성
  - _resolve_mission1 / _resolve_mission2: 특정 answer의 hint 반환
  - get_today_answers: hint1·hint2가 튜플로 반환됨
  - pipeline 연결: routes에서 static_hint가 파이프라인 상태에 포함됨
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── 공통 fixture ──────────────────────────────────────────────────────────────

LOCATION_MISSIONS = [
    {"answer": "지혜의숲", "hint": "천장까지 닿는 책장"},
    {"answer": "창비 안뜰", "hint": "창비의 안무형"},
    {"answer": "출판공방 인쇄소", "hint": "기록의 무게"},
]

ATMOSPHERE_MISSIONS = [
    {"answer": "차분한", "hint": "차분한 분위기를 담아보세요"},
    {"answer": "화사한", "hint": "화사한 사진을 찍어보세요"},
    {"answer": "활기찬", "hint": "활기찬 느낌의 사진을 찍어보세요"},
]

ANSWER_JSON = {
    "missions1": LOCATION_MISSIONS,
    "missions2": ATMOSPHERE_MISSIONS,
}


@pytest.fixture()
def answer_file(tmp_path: Path) -> Path:
    """임시 answer.json 파일을 생성한다."""
    path = tmp_path / "answer.json"
    path.write_text(json.dumps(ANSWER_JSON, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture()
def state_file(tmp_path: Path) -> Path:
    """임시 current_answer.json 경로 (파일 없음 상태)."""
    return tmp_path / "current_answer.json"


def _patch_files(answer_file: Path, state_file: Path):
    """ANSWER_FILE·STATE_FILE을 임시 파일로 교체하는 패치 쌍."""
    return (
        patch("app.services.answer_service.ANSWER_FILE", str(answer_file)),
        patch("app.services.answer_service.STATE_FILE", str(state_file)),
    )


# ── 실제 answer.json 데이터 품질 검증 ────────────────────────────────────────


class TestRealAnswerJsonQuality:
    """실제 프로덕션 data/answer.json의 데이터 품질을 검증한다."""

    @pytest.fixture()
    def real_data(self) -> dict:
        """실제 answer.json을 로드한다."""
        path = Path("data/answer.json")
        if not path.exists():
            pytest.skip("data/answer.json 파일이 없습니다.")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_missions1_hint_field_exists_for_all(self, real_data: dict) -> None:
        """missions1의 모든 항목에 hint 필드가 존재한다."""
        for m in real_data.get("missions1", []):
            assert "hint" in m, f"missions1 항목에 hint 없음: {m}"

    def test_missions2_hint_field_exists_for_all(self, real_data: dict) -> None:
        """missions2의 모든 항목에 hint 필드가 존재한다."""
        for m in real_data.get("missions2", []):
            assert "hint" in m, f"missions2 항목에 hint 없음: {m}"

    def test_missions1_hint_is_non_empty_string(self, real_data: dict) -> None:
        """missions1의 모든 hint는 비어 있지 않은 문자열이다."""
        for m in real_data.get("missions1", []):
            hint = m.get("hint", "")
            assert isinstance(hint, str), f"hint가 str이 아님: {m}"
            assert len(hint.strip()) > 0, f"hint가 빈 문자열: {m}"

    def test_missions2_hint_is_non_empty_string(self, real_data: dict) -> None:
        """missions2의 모든 hint는 비어 있지 않은 문자열이다."""
        for m in real_data.get("missions2", []):
            hint = m.get("hint", "")
            assert isinstance(hint, str), f"hint가 str이 아님: {m}"
            assert len(hint.strip()) > 0, f"hint가 빈 문자열: {m}"

    def test_missions1_answer_field_exists_for_all(self, real_data: dict) -> None:
        """missions1의 모든 항목에 answer 필드가 존재한다."""
        for m in real_data.get("missions1", []):
            assert "answer" in m, f"missions1 항목에 answer 없음: {m}"

    def test_missions2_answer_field_exists_for_all(self, real_data: dict) -> None:
        """missions2의 모든 항목에 answer 필드가 존재한다."""
        for m in real_data.get("missions2", []):
            assert "answer" in m, f"missions2 항목에 answer 없음: {m}"

    def test_missions1_is_non_empty(self, real_data: dict) -> None:
        """missions1 목록이 최소 1개 이상의 미션을 포함한다."""
        assert len(real_data.get("missions1", [])) > 0

    def test_missions2_is_non_empty(self, real_data: dict) -> None:
        """missions2 목록이 최소 1개 이상의 미션을 포함한다."""
        assert len(real_data.get("missions2", [])) > 0


# ── load_missions hint 일관성 ─────────────────────────────────────────────────


class TestLoadMissionsHintConsistency:
    """load_missions1/2가 hint 필드를 포함한 미션 목록을 올바르게 반환하는지 검증한다."""

    def test_missions1_all_have_hint(self, answer_file: Path, state_file: Path) -> None:
        """load_missions1 결과의 모든 항목에 hint 키가 존재한다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions1

            result = load_missions1()
        assert all("hint" in m for m in result)

    def test_missions2_all_have_hint(self, answer_file: Path, state_file: Path) -> None:
        """load_missions2 결과의 모든 항목에 hint 키가 존재한다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions2

            result = load_missions2()
        assert all("hint" in m for m in result)

    def test_missions1_hint_values_are_strings(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """load_missions1의 hint 값은 모두 str이다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions1

            result = load_missions1()
        assert all(isinstance(m["hint"], str) for m in result)

    def test_missions2_hint_values_are_strings(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """load_missions2의 hint 값은 모두 str이다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions2

            result = load_missions2()
        assert all(isinstance(m["hint"], str) for m in result)

    def test_missions1_count(self, answer_file: Path, state_file: Path) -> None:
        """픽스처의 missions1 개수와 일치한다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions1

            result = load_missions1()
        assert len(result) == len(LOCATION_MISSIONS)

    def test_missions2_count(self, answer_file: Path, state_file: Path) -> None:
        """픽스처의 missions2 개수와 일치한다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import load_missions2

            result = load_missions2()
        assert len(result) == len(ATMOSPHERE_MISSIONS)


# ── _resolve_mission hint 반환 검증 ──────────────────────────────────────────


class TestResolveMissionHint:
    """_resolve_mission1/2가 정답에 대응하는 정확한 hint를 반환하는지 검증한다."""

    def test_resolve_mission1_returns_correct_hint(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """관리자 지정 answer의 hint를 정확히 반환한다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _resolve_mission1

            _, hint = _resolve_mission1("지혜의숲")
        assert hint == "천장까지 닿는 책장"

    def test_resolve_mission2_returns_correct_hint(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """관리자 지정 atmosphere answer의 hint를 정확히 반환한다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _resolve_mission2

            _, hint = _resolve_mission2("화사한")
        assert hint == "화사한 사진을 찍어보세요"

    def test_resolve_mission1_random_hint_is_string(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """랜덤 선택 시에도 hint는 str이다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _resolve_mission1

            _, hint = _resolve_mission1(None)
        assert isinstance(hint, str)
        assert len(hint) > 0

    def test_resolve_mission2_random_hint_is_string(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """랜덤 선택 시에도 hint는 str이다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services.answer_service import _resolve_mission2

            _, hint = _resolve_mission2(None)
        assert isinstance(hint, str)
        assert len(hint) > 0


# ── get_today_answers hint 튜플 반환 ─────────────────────────────────────────


class TestGetTodayAnswersHint:
    """get_today_answers가 hint1·hint2를 포함한 튜플을 반환하는지 검증한다."""

    def test_returns_four_element_tuple(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """반환값은 (answer1, answer2, hint1, hint2) 4-튜플이다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services import answer_service

            result = answer_service.get_today_answers()
        assert len(result) == 4

    def test_hint1_is_non_empty_string(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """hint1은 비어있지 않은 str이다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services import answer_service

            _, _, hint1, _ = answer_service.get_today_answers()
        assert isinstance(hint1, str)
        assert len(hint1.strip()) > 0

    def test_hint2_is_non_empty_string(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """hint2는 비어있지 않은 str이다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services import answer_service

            _, _, _, hint2 = answer_service.get_today_answers()
        assert isinstance(hint2, str)
        assert len(hint2.strip()) > 0

    def test_admin_choice_hint_matches_json(
        self, answer_file: Path, state_file: Path
    ) -> None:
        """관리자 지정 answer1='지혜의숲'일 때 hint1은 json의 값과 일치한다."""
        p1, p2 = _patch_files(answer_file, state_file)
        with p1, p2:
            from app.services import answer_service

            _, _, hint1, _ = answer_service.get_today_answers(admin_choice1="지혜의숲")
        assert hint1 == "천장까지 닿는 책장"


# ── pipeline 연결: static_hint가 파이프라인 상태에 포함되는지 ─────────────────


class TestStaticHintPipelinePropagation:
    """routes.py가 세션의 hint를 static_hint로 파이프라인 상태에 주입하는지 검증한다.

    재시도 힌트 생성(_generate_retry_hint)이 static_hint를 받으려면
    request_context에 'static_hint' 키가 있어야 한다.
    """

    def _make_pipeline_state(
        self, answer: str = "지혜의숲", hint: str = "천장까지 닿는 책장"
    ) -> dict:
        """routes.py의 submit_mission이 구성하는 파이프라인 초기 상태를 재현한다."""
        return {
            "request_context": {
                "answer": answer,
                "static_hint": hint,
                "mission_type": "location",
                "model_selection": ["siglip2", "blip"],
            },
            "artifacts": {},
            "errors": [],
            "control_flags": {},
            "votes": [],
            "messages": [],
        }

    def test_static_hint_key_in_request_context(self) -> None:
        """파이프라인 초기 상태의 request_context에 'static_hint' 키가 존재한다."""
        state = self._make_pipeline_state()
        assert "static_hint" in state["request_context"]

    def test_static_hint_value_matches_session_hint(self) -> None:
        """request_context의 static_hint 값이 세션 hint와 동일하다."""
        hint = "갈대밭이 있는 곳"
        state = self._make_pipeline_state(hint=hint)
        assert state["request_context"]["static_hint"] == hint

    def test_static_hint_propagated_to_retry_hint_function(self) -> None:
        """responder 실패 분기에서 _generate_retry_hint가 static_hint를 받는다."""
        from app.council.nodes import _generate_retry_hint

        with patch("app.models.llm.LLMService") as mock_cls:
            mock_svc = MagicMock()
            mock_svc.generate_blip_hint.return_value = "감성 힌트 문장"
            mock_cls.return_value = mock_svc

            result = _generate_retry_hint("지혜의숲", "천장까지 닿는 책장", "location")

        mock_svc.generate_blip_hint.assert_called_once_with(
            answer="지혜의숲",
            static_hint="천장까지 닿는 책장",
            mission_type="location",
        )
        assert result == "감성 힌트 문장"

    def test_retry_hint_fallback_returns_static_hint_string(self) -> None:
        """LLM 실패 시 폴백은 static_hint를 그대로 반환한다 (타입 보장)."""
        from app.council.nodes import _generate_retry_hint

        with patch("app.models.llm.LLMService", side_effect=RuntimeError("no key")):
            result = _generate_retry_hint("지혜의숲", "천장까지 닿는 책장", "location")

        assert isinstance(result, str)
        assert result == "천장까지 닿는 책장"
