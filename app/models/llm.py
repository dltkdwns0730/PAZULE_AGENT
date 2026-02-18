"""LLM helper service for hint generation and atmosphere verification."""

from __future__ import annotations

import json

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


class LLMService:
    """Purpose: `LLMService` ??? ??? ?? ??? ???
    Context: ?? ???? ?? ??? ??? ??
    Attrs: ?? ?? ???? ?? ??? ???"""
    def __init__(self):
        """Caller: ?? ?? ???? ???
        Purpose: `__init__` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: None
        Note: ?? ?? ?? ???? ???"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )

        self.blip_hint_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "당신은 장소 미션 힌트 생성기다. "
                        "정답을 직접 말하지 말고 실패 근거를 바탕으로 간접 힌트를 제공하라."
                    ),
                ),
                (
                    "user",
                    (
                        "정답: {answer}\n"
                        "실패 근거: {failed_info}\n"
                        "위 정보를 기반으로 1~2문장 힌트를 작성하라."
                    ),
                ),
            ]
        )

        self.mood_verification_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "당신은 분위기 판정 에이전트다. "
                        "입력 컨텍스트와 목표 감성의 일치 여부를 판단하고 JSON으로만 답하라."
                    ),
                ),
                (
                    "user",
                    (
                        "목표 감성: {answer}\n"
                        "감성 정의: {keyword_definitions}\n"
                        "이미지 컨텍스트:\n{context}\n\n"
                        'Return JSON: {"success": true/false, "reason": "..."}'
                    ),
                ),
            ]
        )

    def generate_blip_hint(self, answer: str, failed_questions: list) -> str:
        """Caller: ?? ?? ???? ???
        Purpose: `generate_blip_hint` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: answer: ???? ???? ??; failed_questions: ???? ???? ??
        Note: ?? ?? ?? ???? ???"""
        failed_info = self._format_blip_failures(failed_questions)
        try:
            chain = self.blip_hint_prompt | self.llm
            response = chain.invoke({"answer": answer, "failed_info": failed_info})
            return response.content
        except Exception:
            return "핵심 특징을 더 또렷하게 담아 다시 촬영해 보세요."

    def verify_mood(self, answer: str, context: str) -> dict:
        """Caller: ?? ?? ???? ???
        Purpose: `verify_mood` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: answer: ???? ???? ??; context: ???? ???? ??
        Note: ?? ?? ?? ???? ???"""
        from app.core.keyword import feedback_guide

        definition = feedback_guide.get(answer, {}).get("desc", "정의 없음")
        chain = self.mood_verification_prompt | self.llm

        try:
            response = chain.invoke(
                {
                    "answer": answer,
                    "context": context,
                    "keyword_definitions": f"{answer}: {definition}",
                }
            )
            content = response.content.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(content)
            if "success" not in parsed:
                parsed["success"] = False
            if "reason" not in parsed:
                parsed["reason"] = "판정 근거를 생성하지 못했습니다."
            return parsed
        except Exception:
            return {
                "success": False,
                "reason": "분위기 판정에 실패했습니다. 구도와 색감을 바꿔 다시 촬영해 주세요.",
            }

    def _format_blip_failures(self, questions: list) -> str:
        """Caller: ?? ?? ???? ???
        Purpose: `_format_blip_failures` ?? ??? ????
        Returns: ?? ?? ?? ??
        Deps: ?? ??? ??
        Args: questions: ???? ???? ??
        Note: ?? ?? ?? ???? ???"""
        if not questions:
            return "(실패 근거 없음)"
        result = []
        for q in questions:
            result.append(
                f"질문: {q.get('question')}, "
                f"모델 답: {q.get('model_answer')}, "
                f"기대 답: {q.get('expected_answer')}"
            )
        return "\n".join(result)


llm_service = LLMService()
