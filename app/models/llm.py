"""LLM 기반 힌트 생성 및 감성 검증 서비스."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.prompts.registry import PromptVersion, with_prompt

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 기반 힌트 생성 및 감성 검증 서비스.

    Gemini API를 우선 사용하고, 없을 경우 OpenAI로 폴백한다.
    """

    def __init__(self) -> None:
        """LLM 프로바이더를 초기화한다.

        Raises:
            ImportError: GEMINI_API_KEY 설정 시 langchain-google-genai 미설치.
            RuntimeError: API 키가 모두 설정되지 않은 경우.
        """
        if settings.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                self.llm = ChatGoogleGenerativeAI(
                    model=settings.LLM_MODEL_ID or "gemini-2.5-flash",
                    temperature=0.7,
                    api_key=settings.GEMINI_API_KEY,
                    timeout=settings.API_TIMEOUT_SECONDS,
                    max_retries=settings.API_MAX_RETRIES,
                )
            except ImportError:
                raise ImportError(
                    "GEMINI_API_KEY is set but langchain-google-genai is not installed. "
                    "Run: uv pip install langchain-google-genai"
                )
        elif settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL_ID or "gpt-4o-mini",
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.API_TIMEOUT_SECONDS,
                max_retries=settings.API_MAX_RETRIES,
            )
        else:
            raise RuntimeError(
                "LLM 초기화 실패: GEMINI_API_KEY 또는 OPENAI_API_KEY를 .env에 설정하세요."
            )

    @with_prompt("hint_generation")
    def generate_blip_hint(
        self, *, answer: str, failed_info: str, prompt: PromptVersion | None = None
    ) -> str:
        """BLIP 오답 정보를 기반으로 힌트를 생성한다.

        Args:
            answer: 미션 정답 키워드.
            failed_info: 오답 내역 텍스트.
            prompt: 주입된 PromptVersion (데코레이터가 자동 주입).

        Returns:
            생성된 힌트 문자열.
        """
        chat_prompt = ChatPromptTemplate.from_messages(
            [("system", prompt.system), ("user", prompt.user)]
        )
        chain = chat_prompt | self.llm
        response = chain.invoke({})
        return response.content

    @with_prompt("mood_verification")
    def verify_mood(
        self,
        *,
        answer: str,
        context: str,
        keyword_definitions: str,
        prompt: PromptVersion | None = None,
    ) -> dict[str, Any]:
        """감성 키워드와 이미지 컨텍스트를 비교하여 일치 여부를 판단한다.

        Args:
            answer: 미션 정답 키워드.
            context: BLIP으로 추출한 시각 컨텍스트.
            keyword_definitions: 키워드 정의 텍스트.
            prompt: 주입된 PromptVersion (데코레이터가 자동 주입).

        Returns:
            {'success': bool, 'reason': str} 형태의 판정 결과.
        """
        chat_prompt = ChatPromptTemplate.from_messages(
            [("system", prompt.system), ("user", prompt.user)]
        )
        chain = chat_prompt | self.llm

        try:
            response = chain.invoke({})
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as exc:
            logger.error("LLM 검증 오류: %s", exc)
            return {
                "success": False,
                "reason": "AI 판단 중 오류가 발생했습니다.",
            }

    def generate_blip_hint_from_questions(
        self, answer: str, failed_questions: list[dict[str, str]]
    ) -> str:
        """기존 인터페이스 호환: failed_questions를 포맷팅하여 힌트를 생성한다.

        Args:
            answer: 미션 정답 키워드.
            failed_questions: 오답 질문 딕셔너리 목록.

        Returns:
            생성된 힌트 문자열.
        """
        failed_info = self._format_blip_failures(failed_questions)
        return self.generate_blip_hint(answer=answer, failed_info=failed_info)

    def verify_mood_with_answer(self, answer: str, context: str) -> dict[str, Any]:
        """기존 인터페이스 호환: answer와 context로 감성 검증을 수행한다.

        Args:
            answer: 미션 정답 키워드.
            context: BLIP으로 추출한 시각 컨텍스트.

        Returns:
            {'success': bool, 'reason': str} 형태의 판정 결과.
        """
        from app.core.keyword import feedback_guide

        definition = feedback_guide.get(answer, {}).get("desc", "정의 없음")
        keyword_definitions = f"{answer}: {definition}"
        return self.verify_mood(
            answer=answer, context=context, keyword_definitions=keyword_definitions
        )

    def _format_blip_failures(self, questions: list[dict[str, str]]) -> str:
        """BLIP 오답 리스트를 텍스트로 포맷한다.

        Args:
            questions: 오답 질문 딕셔너리 목록.

        Returns:
            포맷된 오답 정보 문자열.
        """
        if not questions:
            return "(부족한 특징 정보 없음)"
        result = []
        for q in questions:
            result.append(
                f"질문: {q.get('question')}, "
                f"모델 답변: {q.get('model_answer')}, "
                f"기대 답변: {q.get('expected_answer')}"
            )
        return "\n".join(result)


llm_service = LLMService()
