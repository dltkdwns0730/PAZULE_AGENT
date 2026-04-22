"""LLMService 단위 테스트.

검증 대상:
  - LLMService.__init__: Gemini / OpenAI / 키 없음 / ImportError 분기
  - verify_mood: 정상 JSON 파싱 / 예외 폴백
  - generate_blip_hint_from_questions: generate_blip_hint 위임
  - verify_mood_with_answer: 키워드 정의 조합 → verify_mood 위임
  - _format_blip_failures: 빈 목록 / 항목 있음
  - get_llm_service: lazy singleton 초기화
"""

from __future__ import annotations

import json
import sys
from types import ModuleType
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from app.prompts.registry import PromptVersion


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────


def _make_svc(llm_response: str = "힌트") -> tuple:
    """테스트용 LLMService 인스턴스를 반환한다 (API 호출 없음)."""
    from app.models.llm import LLMService

    mock_llm = MagicMock(spec=ChatOpenAI)
    mock_llm.invoke.return_value = MagicMock(content=llm_response)

    with patch("app.models.llm.settings") as mock_s:
        mock_s.GEMINI_API_KEY = None
        mock_s.OPENAI_API_KEY = "fake-key"
        mock_s.LLM_MODEL_ID = None
        mock_s.API_TIMEOUT_SECONDS = 10
        mock_s.API_MAX_RETRIES = 1
        svc = LLMService.__new__(LLMService)
        svc.llm = mock_llm
    return svc, mock_llm


# ── LLMService.__init__ ───────────────────────────────────────────────────────


class TestLLMServiceInit:
    """LLMService 초기화 분기를 검증한다."""

    def test_openai_branch_sets_llm(self) -> None:
        """OPENAI_API_KEY만 있으면 ChatOpenAI 인스턴스가 설정된다."""
        from app.models.llm import LLMService

        with (
            patch("app.models.llm.settings") as mock_s,
            patch("app.models.llm.ChatOpenAI") as mock_cls,
        ):
            mock_s.GEMINI_API_KEY = None
            mock_s.OPENAI_API_KEY = "sk-test"
            mock_s.LLM_MODEL_ID = None
            mock_s.API_TIMEOUT_SECONDS = 30
            mock_s.API_MAX_RETRIES = 2
            mock_cls.return_value = MagicMock()
            svc = LLMService()

        mock_cls.assert_called_once()
        assert svc.llm is mock_cls.return_value

    def test_openai_uses_custom_model_id(self) -> None:
        """LLM_MODEL_ID가 있으면 그 값을 model 인수로 전달한다."""
        from app.models.llm import LLMService

        with (
            patch("app.models.llm.settings") as mock_s,
            patch("app.models.llm.ChatOpenAI") as mock_cls,
        ):
            mock_s.GEMINI_API_KEY = None
            mock_s.OPENAI_API_KEY = "sk-test"
            mock_s.LLM_MODEL_ID = "gpt-4-turbo"
            mock_s.API_TIMEOUT_SECONDS = 30
            mock_s.API_MAX_RETRIES = 2
            mock_cls.return_value = MagicMock()
            LLMService()

        _, kwargs = mock_cls.call_args
        assert kwargs.get("model") == "gpt-4-turbo"

    def test_no_api_key_raises_runtime_error(self) -> None:
        """API 키가 모두 없으면 RuntimeError를 발생시킨다."""
        from app.models.llm import LLMService

        with (
            patch("app.models.llm.settings") as mock_s,
            pytest.raises(RuntimeError, match="GEMINI_API_KEY 또는 OPENAI_API_KEY"),
        ):
            mock_s.GEMINI_API_KEY = None
            mock_s.OPENAI_API_KEY = None
            LLMService()

    def test_gemini_branch_sets_llm(self) -> None:
        """GEMINI_API_KEY가 있으면 ChatGoogleGenerativeAI가 설정된다."""
        from app.models.llm import LLMService

        mock_genai_cls = MagicMock()
        mock_genai_instance = MagicMock()
        mock_genai_cls.return_value = mock_genai_instance

        fake_genai_module = ModuleType("langchain_google_genai")
        fake_genai_module.ChatGoogleGenerativeAI = mock_genai_cls  # type: ignore[attr-defined]

        with (
            patch("app.models.llm.settings") as mock_s,
            patch.dict(sys.modules, {"langchain_google_genai": fake_genai_module}),
        ):
            mock_s.GEMINI_API_KEY = "gemini-abc"
            mock_s.LLM_MODEL_ID = None
            mock_s.API_TIMEOUT_SECONDS = 10
            mock_s.API_MAX_RETRIES = 1
            svc = LLMService()

        mock_genai_cls.assert_called_once()
        assert svc.llm is mock_genai_instance

    def test_gemini_import_error_raised(self) -> None:
        """langchain-google-genai 미설치 시 ImportError를 발생시킨다."""
        from app.models.llm import LLMService

        with (
            patch("app.models.llm.settings") as mock_s,
            patch.dict(sys.modules, {"langchain_google_genai": None}),
            pytest.raises(ImportError, match="langchain-google-genai"),
        ):
            mock_s.GEMINI_API_KEY = "gemini-abc"
            mock_s.LLM_MODEL_ID = None
            mock_s.API_TIMEOUT_SECONDS = 10
            mock_s.API_MAX_RETRIES = 1
            LLMService()


# ── verify_mood ───────────────────────────────────────────────────────────────


def _mock_prompt(
    system: str = "You are a mood analyzer.", user: str = "Emotion: 화사한"
) -> "PromptVersion":
    """LangChain이 오해하는 중괄호 없는 깨끗한 PromptVersion을 반환한다."""
    from app.prompts.registry import PromptVersion

    return PromptVersion(
        name="mood_verification",
        version="3.0",
        variant="default",
        system=system,
        user=user,
    )


class TestVerifyMood:
    """LLMService.verify_mood 분기를 검증한다.

    mood_verification.yaml 예시 JSON의 이중 중괄호({{ }})가 .format() 후
    단일 중괄호({ })로 변환돼 LangChain이 템플릿 변수로 오해한다.
    따라서 PromptRegistry.render를 모킹해 깨끗한 PromptVersion을 주입한다.
    """

    def test_returns_parsed_json_on_success(self) -> None:
        """LLM 응답이 유효한 JSON이면 파싱된 딕셔너리를 반환한다."""
        payload = {"success": True, "reason": "분위기 일치"}
        svc, mock_llm = _make_svc()
        mock_llm.invoke.return_value = MagicMock(content=json.dumps(payload))

        with patch(
            "app.prompts.registry.PromptRegistry.render", return_value=_mock_prompt()
        ):
            result = svc.verify_mood(
                answer="화사한",
                context="bright sunny scene",
                keyword_definitions="화사한: 밝고 생동감 있는",
            )

        assert result["success"] is True
        assert result["reason"] == "분위기 일치"

    def test_strips_json_code_fence(self) -> None:
        """LLM 응답에 ```json 코드 펜스가 있어도 올바르게 파싱한다."""
        payload = {"success": False, "reason": "어두움"}
        raw = f"```json\n{json.dumps(payload)}\n```"
        svc, mock_llm = _make_svc()
        mock_llm.invoke.return_value = MagicMock(content=raw)

        with patch(
            "app.prompts.registry.PromptRegistry.render", return_value=_mock_prompt()
        ):
            result = svc.verify_mood(
                answer="화사한",
                context="dark scene",
                keyword_definitions="화사한: 밝고 생동감 있는",
            )

        assert result["success"] is False
        assert result["reason"] == "어두움"

    def test_exception_returns_fallback(self) -> None:
        """LLM 호출 중 예외 발생 시 오류 딕셔너리를 반환한다."""
        svc, mock_llm = _make_svc()
        mock_llm.invoke.side_effect = RuntimeError("timeout")

        with patch(
            "app.prompts.registry.PromptRegistry.render", return_value=_mock_prompt()
        ):
            result = svc.verify_mood(
                answer="차분한",
                context="noisy image",
                keyword_definitions="차분한: 조용하고 고요한",
            )

        assert result["success"] is False
        assert "오류" in result["reason"]

    def test_invalid_json_returns_fallback(self) -> None:
        """LLM 응답이 유효하지 않은 JSON이면 오류 딕셔너리를 반환한다."""
        svc, mock_llm = _make_svc()
        mock_llm.invoke.return_value = MagicMock(content="not json at all")

        with patch(
            "app.prompts.registry.PromptRegistry.render", return_value=_mock_prompt()
        ):
            result = svc.verify_mood(
                answer="활기찬",
                context="lively scene",
                keyword_definitions="활기찬: 에너지 넘치는",
            )

        assert result["success"] is False


# ── generate_blip_hint_from_questions ────────────────────────────────────────


class TestGenerateBlipHintFromQuestions:
    """generate_blip_hint_from_questions가 generate_blip_hint에 위임하는지 검증한다."""

    def test_delegates_to_generate_blip_hint(self) -> None:
        """generate_blip_hint가 올바른 인수로 호출된다."""
        svc, _ = _make_svc()
        svc.generate_blip_hint = MagicMock(return_value="위임 힌트")

        result = svc.generate_blip_hint_from_questions(
            answer="지혜의숲",
            failed_questions=[{"q": "a"}],
            static_hint="책장",
            mission_type="location",
        )

        svc.generate_blip_hint.assert_called_once_with(
            answer="지혜의숲",
            static_hint="책장",
            mission_type="location",
        )
        assert result == "위임 힌트"

    def test_default_static_hint_and_mission_type(self) -> None:
        """static_hint·mission_type 기본값이 generate_blip_hint에 전달된다."""
        svc, _ = _make_svc()
        svc.generate_blip_hint = MagicMock(return_value="기본 힌트")

        svc.generate_blip_hint_from_questions(answer="화사한", failed_questions=[])

        _, kwargs = svc.generate_blip_hint.call_args
        assert kwargs["static_hint"] == ""
        assert kwargs["mission_type"] == "location"


# ── verify_mood_with_answer ───────────────────────────────────────────────────


class TestVerifyMoodWithAnswer:
    """verify_mood_with_answer가 feedback_guide 정의를 조합하는지 검증한다."""

    def test_calls_verify_mood_with_combined_definition(self) -> None:
        """알려진 answer의 desc가 keyword_definitions에 포함된다."""
        svc, _ = _make_svc()
        svc.verify_mood = MagicMock(return_value={"success": True, "reason": "OK"})

        with patch(
            "app.core.keyword.feedback_guide", {"화사한": {"desc": "밝은 느낌"}}
        ):
            svc.verify_mood_with_answer("화사한", "bright image")

        _, kwargs = svc.verify_mood.call_args
        assert "화사한" in kwargs["keyword_definitions"]
        assert "밝은 느낌" in kwargs["keyword_definitions"]

    def test_unknown_answer_uses_default_definition(self) -> None:
        """feedback_guide에 없는 answer는 '정의 없음'을 사용한다."""
        svc, _ = _make_svc()
        svc.verify_mood = MagicMock(return_value={"success": False, "reason": "X"})

        with patch("app.core.keyword.feedback_guide", {}):
            svc.verify_mood_with_answer("알수없음", "context")

        _, kwargs = svc.verify_mood.call_args
        assert "정의 없음" in kwargs["keyword_definitions"]

    def test_returns_verify_mood_result(self) -> None:
        """verify_mood 반환값을 그대로 반환한다."""
        svc, _ = _make_svc()
        expected = {"success": True, "reason": "일치"}
        svc.verify_mood = MagicMock(return_value=expected)

        with patch("app.core.keyword.feedback_guide", {}):
            result = svc.verify_mood_with_answer("활기찬", "ctx")

        assert result is expected


# ── _format_blip_failures ─────────────────────────────────────────────────────


class TestFormatBlipFailures:
    """_format_blip_failures의 빈 목록 / 항목 포맷을 검증한다."""

    def test_empty_list_returns_placeholder(self) -> None:
        """빈 목록이면 고정 안내 문자열을 반환한다."""
        svc, _ = _make_svc()
        result = svc._format_blip_failures([])
        assert result == "(부족한 특징 정보 없음)"

    def test_single_item_formatted(self) -> None:
        """단일 항목이 올바른 형식으로 포맷된다."""
        svc, _ = _make_svc()
        questions = [{"question": "Q1", "model_answer": "A", "expected_answer": "B"}]
        result = svc._format_blip_failures(questions)
        assert "Q1" in result
        assert "A" in result
        assert "B" in result

    def test_multiple_items_joined_by_newline(self) -> None:
        """여러 항목이 개행으로 구분된다."""
        svc, _ = _make_svc()
        questions = [
            {"question": "Q1", "model_answer": "A", "expected_answer": "B"},
            {"question": "Q2", "model_answer": "C", "expected_answer": "D"},
        ]
        result = svc._format_blip_failures(questions)
        lines = result.split("\n")
        assert len(lines) == 2

    def test_missing_keys_handled_gracefully(self) -> None:
        """딕셔너리 키가 없어도 None으로 처리되고 예외 없음."""
        svc, _ = _make_svc()
        result = svc._format_blip_failures([{}])
        assert isinstance(result, str)
        assert "None" in result


# ── get_llm_service ───────────────────────────────────────────────────────────


class TestGetLlmService:
    """get_llm_service lazy singleton을 검증한다."""

    def setup_method(self) -> None:
        """각 테스트 전에 싱글턴 캐시를 초기화한다."""
        import app.models.llm as llm_module

        llm_module._llm_service = None

    def teardown_method(self) -> None:
        import app.models.llm as llm_module

        llm_module._llm_service = None

    def test_returns_llm_service_instance(self) -> None:
        """LLMService 인스턴스를 반환한다."""
        from app.models.llm import LLMService, get_llm_service

        mock_svc = MagicMock(spec=LLMService)
        with patch("app.models.llm.LLMService", return_value=mock_svc):
            result = get_llm_service()
        assert result is mock_svc

    def test_singleton_returns_same_instance(self) -> None:
        """두 번 호출해도 같은 인스턴스를 반환한다."""
        from app.models.llm import LLMService, get_llm_service

        mock_svc = MagicMock(spec=LLMService)
        with patch("app.models.llm.LLMService", return_value=mock_svc):
            first = get_llm_service()
            second = get_llm_service()
        assert first is second

    def test_llm_service_constructor_called_once(self) -> None:
        """LLMService() 생성자는 최초 1회만 호출된다."""
        from app.models.llm import LLMService, get_llm_service

        mock_svc = MagicMock(spec=LLMService)
        with patch("app.models.llm.LLMService", return_value=mock_svc) as mock_cls:
            get_llm_service()
            get_llm_service()
            get_llm_service()
        mock_cls.assert_called_once()
