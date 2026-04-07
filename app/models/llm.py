"""LLM 기반 힌트 생성 및 감성 검증 서비스."""

from __future__ import annotations

import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.prompts.registry import PromptVersion, with_prompt


class LLMService:
    """LLM 기반 힌트 생성 및 감성 검증 서비스."""

    def __init__(self):
        # 1. Gemini API (우선순위 1 — 기본 LLM 프로바이더)
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
        # 2. Fallback: OpenAI
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
        """BLIP 오답 정보를 기반으로 힌트를 생성한다."""
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
    ) -> dict:
        """감성 키워드와 이미지 컨텍스트를 비교하여 일치 여부를 판단한다."""
        chat_prompt = ChatPromptTemplate.from_messages(
            [("system", prompt.system), ("user", prompt.user)]
        )
        chain = chat_prompt | self.llm

        try:
            response = chain.invoke({})
            content = (
                response.content.replace("```json", "").replace("```", "").strip()
            )
            return json.loads(content)
        except Exception as e:
            print(f"LLM 검증 오류: {e}")
            return {
                "success": False,
                "reason": "AI 판단 중 오류가 발생했습니다.",
            }

    def generate_blip_hint_from_questions(
        self, answer: str, failed_questions: list
    ) -> str:
        """기존 인터페이스 호환: failed_questions를 포맷팅하여 힌트를 생성한다."""
        failed_info = self._format_blip_failures(failed_questions)
        return self.generate_blip_hint(answer=answer, failed_info=failed_info)

    def verify_mood_with_answer(self, answer: str, context: str) -> dict:
        """기존 인터페이스 호환: answer와 context로 감성 검증을 수행한다."""
        from app.core.keyword import feedback_guide

        definition = feedback_guide.get(answer, {}).get("desc", "정의 없음")
        keyword_definitions = f"{answer}: {definition}"
        return self.verify_mood(
            answer=answer, context=context, keyword_definitions=keyword_definitions
        )

    def _format_blip_failures(self, questions: list) -> str:
        """BLIP 오답 리스트를 텍스트로 포맷한다."""
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
