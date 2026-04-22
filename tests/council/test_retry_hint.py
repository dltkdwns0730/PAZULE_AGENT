"""재시도 힌트 생성 단위 테스트.

검증 대상:
  - _generate_retry_hint: LLM 호출 / 실패 시 폴백
  - LLMService.generate_blip_hint: 프롬프트 렌더링 → LLM 호출 → 문자열 반환
  - prompt_hint_generation.yaml: 필수 변수 존재 / default variant 활성 여부
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from langchain_openai import ChatOpenAI

from app.council.nodes import _generate_retry_hint


# ── _generate_retry_hint ──────────────────────────────────────────────────────


class TestGenerateRetryHint:
    """nodes._generate_retry_hint 동작 검증."""

    def _patch_llm(self, return_value: str = "감성 힌트"):
        """LLMService를 모킹하는 컨텍스트 매니저를 반환한다."""
        mock_svc = MagicMock()
        mock_svc.generate_blip_hint.return_value = return_value
        return patch("app.models.llm.LLMService", return_value=mock_svc), mock_svc

    def test_returns_llm_output(self) -> None:
        """LLM이 성공하면 해당 문자열을 그대로 반환한다."""
        ctx, mock_svc = self._patch_llm("끝없이 높은 책장이 있는 곳을 찾아보세요.")
        with ctx:
            result = _generate_retry_hint("지혜의숲", "책이 가득한 곳", "location")
        assert result == "끝없이 높은 책장이 있는 곳을 찾아보세요."

    def test_calls_llm_with_correct_args(self) -> None:
        """generate_blip_hint에 answer, static_hint, mission_type이 정확히 전달된다."""
        ctx, mock_svc = self._patch_llm()
        with ctx:
            _generate_retry_hint("화사한", "밝은 느낌의 사진", "atmosphere")
        mock_svc.generate_blip_hint.assert_called_once_with(
            answer="화사한",
            static_hint="밝은 느낌의 사진",
            mission_type="atmosphere",
        )

    def test_fallback_to_static_hint_on_llm_failure(self) -> None:
        """LLM 초기화 실패 시 static_hint를 반환한다."""
        with patch("app.models.llm.LLMService", side_effect=RuntimeError("no API key")):
            result = _generate_retry_hint("지혜의숲", "책이 가득한 곳", "location")
        assert result == "책이 가득한 곳"

    def test_fallback_to_static_hint_on_generate_failure(self) -> None:
        """generate_blip_hint 호출 실패 시에도 static_hint를 반환한다."""
        mock_svc = MagicMock()
        mock_svc.generate_blip_hint.side_effect = Exception("LLM timeout")
        with patch("app.models.llm.LLMService", return_value=mock_svc):
            result = _generate_retry_hint("지혜의숲", "책이 가득한 곳", "location")
        assert result == "책이 가득한 곳"

    def test_fallback_default_message_when_static_hint_empty(self) -> None:
        """LLM 실패 + static_hint 빈 문자열이면 기본 안내 문구를 반환한다."""
        with patch("app.models.llm.LLMService", side_effect=RuntimeError("no key")):
            result = _generate_retry_hint("지혜의숲", "", "location")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_string_type(self) -> None:
        """반환값은 항상 str이다."""
        ctx, _ = self._patch_llm("힌트 문장")
        with ctx:
            result = _generate_retry_hint("차분한", "고요한 공간", "atmosphere")
        assert isinstance(result, str)

    def test_location_mission_forwarded_correctly(self) -> None:
        """location 미션 유형이 그대로 LLM에 전달된다."""
        ctx, mock_svc = self._patch_llm()
        with ctx:
            _generate_retry_hint("네모탑", "사각형 구조물", "location")
        _, kwargs = mock_svc.generate_blip_hint.call_args
        assert kwargs["mission_type"] == "location"

    def test_atmosphere_mission_forwarded_correctly(self) -> None:
        """atmosphere 미션 유형이 그대로 LLM에 전달된다."""
        ctx, mock_svc = self._patch_llm()
        with ctx:
            _generate_retry_hint("활기찬", "에너지 넘치는 장면", "atmosphere")
        _, kwargs = mock_svc.generate_blip_hint.call_args
        assert kwargs["mission_type"] == "atmosphere"


# ── LLMService.generate_blip_hint ─────────────────────────────────────────────


class TestGenerateBlipHint:
    """LLMService.generate_blip_hint 동작 검증 (LLM 호출 mock)."""

    def _make_service(self, llm_response: str = "힌트"):
        """LLM이 모킹된 LLMService 인스턴스를 반환한다."""
        from app.models.llm import LLMService

        # spec=ChatOpenAI 필수: LangChain이 Runnable 타입 체크를 통과해야
        # RunnableLambda 래핑 없이 .invoke()를 직접 호출한다.
        mock_llm = MagicMock(spec=ChatOpenAI)
        mock_llm.invoke.return_value = MagicMock(content=llm_response)

        with patch("app.models.llm.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = None
            mock_settings.OPENAI_API_KEY = "fake-key"
            mock_settings.LLM_MODEL_ID = None
            mock_settings.API_TIMEOUT_SECONDS = 10
            mock_settings.API_MAX_RETRIES = 1
            svc = LLMService.__new__(LLMService)
            svc.llm = mock_llm
        return svc, mock_llm

    def test_returns_string(self, tmp_path: Path) -> None:
        """반환값은 str이다."""
        from app.prompts.registry import PromptRegistry

        PromptRegistry._instance = None
        PromptRegistry._initialized = False

        reg = PromptRegistry.get_instance()
        template_path = Path(
            "app/prompts/templates/prompt_hint_generation.yaml"
        ).resolve()
        reg.load(template_path)

        svc, mock_llm = self._make_service("자연스러운 힌트 문장")
        mock_llm.invoke.return_value = MagicMock(content="자연스러운 힌트 문장")

        result = svc.generate_blip_hint(
            answer="지혜의숲",
            static_hint="책이 가득한 곳",
            mission_type="location",
        )
        assert isinstance(result, str)
        assert len(result) > 0

        PromptRegistry._instance = None
        PromptRegistry._initialized = False

    def test_llm_invoke_called(self, tmp_path: Path) -> None:
        """LLM chain.invoke가 실제로 호출된다."""
        from app.prompts.registry import PromptRegistry

        PromptRegistry._instance = None
        PromptRegistry._initialized = False

        reg = PromptRegistry.get_instance()
        template_path = Path(
            "app/prompts/templates/prompt_hint_generation.yaml"
        ).resolve()
        reg.load(template_path)

        svc, mock_llm = self._make_service()
        svc.generate_blip_hint(
            answer="화사한",
            static_hint="밝고 생동감 있는 장면",
            mission_type="atmosphere",
        )
        assert mock_llm.invoke.called

        PromptRegistry._instance = None
        PromptRegistry._initialized = False


# ── prompt_hint_generation.yaml 구조 검증 ─────────────────────────────────────


class TestPromptTemplate:
    """prompt_hint_generation.yaml 파일 구조를 검증한다."""

    @pytest.fixture()
    def template(self) -> dict:
        path = Path("app/prompts/templates/prompt_hint_generation.yaml")
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_default_variant_exists(self, template: dict) -> None:
        """default variant가 정의되어 있다."""
        assert "default" in template["variants"]

    def test_default_variant_is_active(self, template: dict) -> None:
        """default variant의 weight가 0보다 크다 (활성 상태)."""
        assert template["variants"]["default"]["weight"] > 0.0

    def test_user_template_has_answer_placeholder(self, template: dict) -> None:
        """user 템플릿에 {answer} 변수가 존재한다."""
        user = template["variants"]["default"]["user"]
        assert "{answer}" in user

    def test_user_template_has_static_hint_placeholder(self, template: dict) -> None:
        """user 템플릿에 {static_hint} 변수가 존재한다."""
        user = template["variants"]["default"]["user"]
        assert "{static_hint}" in user

    def test_user_template_has_mission_type_placeholder(self, template: dict) -> None:
        """user 템플릿에 {mission_type} 변수가 존재한다."""
        user = template["variants"]["default"]["user"]
        assert "{mission_type}" in user

    def test_system_prompt_is_non_empty(self, template: dict) -> None:
        """system 프롬프트가 비어 있지 않다."""
        system = template["variants"]["default"]["system"]
        assert isinstance(system, str)
        assert len(system.strip()) > 0

    def test_name_is_hint_generation(self, template: dict) -> None:
        """템플릿 이름이 'hint_generation'이다."""
        assert template["name"] == "hint_generation"
