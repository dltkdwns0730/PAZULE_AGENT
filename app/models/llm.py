import json

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


class LLMService:
    """LLM 기반 힌트 생성 및 감성 검증 서비스"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )

        # 미션1: BLIP 오답 기반 힌트 생성 프롬프트
        self.blip_hint_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "당신은 파주 출판단지 보물찾기 게임의 힌트 제공자입니다.\n"
                    "사용자가 촬영한 사진이 정답 랜드마크가 아닐 때, "
                    "정답을 직접 언급하지 않고 추상적이고 시적인 힌트를 제공하세요.\n"
                    "BLIP VQA 분석 결과를 바탕으로 부족한 특징을 은유적으로 설명하세요.",
                ),
                (
                    "user",
                    "정답 랜드마크: {answer}\n분석 결과: {failed_info}\n\n"
                    "위 정보를 바탕으로 창의적인 힌트를 작성해주세요.",
                ),
            ]
        )

        # 미션2: 감성 사진 검증 프롬프트
        self.mood_verification_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "당신은 감성 사진 심사위원입니다.\n"
                    "주어진 '이미지 시각적 맥락(BLIP 분석)'을 읽고, "
                    "이 사진이 목표로 하는 '감성 키워드'와 일치하는지 판단하세요.\n"
                    "참고로 키워드의 정의는 다음과 같습니다.\n"
                    "{keyword_definitions}\n\n"
                    "판단 결과는 반드시 JSON 형식으로 반환해야 합니다.\n"
                    '{{"success": true/false, '
                    '"reason": "판단 근거를 한 문장으로 작성"}}\n'
                    "엄격하게 판단하지 말고, 분위기가 어느 정도 느껴지면 성공으로 인정해주세요.",
                ),
                (
                    "user",
                    "목표 감성: {answer}\n이미지 시각적 맥락:\n{context}",
                ),
            ]
        )

    def generate_blip_hint(self, answer: str, failed_questions: list) -> str:
        """BLIP 오답 정보를 기반으로 힌트를 생성한다."""
        failed_info = self._format_blip_failures(failed_questions)
        chain = self.blip_hint_prompt | self.llm
        response = chain.invoke({"answer": answer, "failed_info": failed_info})
        return response.content

    def verify_mood(self, answer: str, context: str) -> dict:
        """감성 키워드와 이미지 컨텍스트를 비교하여 일치 여부를 판단한다."""
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
