from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.council.state import CouncilState
from app.services.mission_service import run_mission1, run_mission2

llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)


class SecurityAgent:
    """입력 검증 에이전트 -- 안전성/유효성 검사를 수행한다."""

    def check_safety(self, state: CouncilState):
        """요청과 이미지의 안전성을 검증한다.

        현재는 placeholder(통과) 상태이며,
        향후 Prompt Injection 탐지 및 NSFW 필터링을 추가할 예정.
        """
        print("[Security Agent] 안전성 검사 중...")
        # TODO: Llama Guard / Vision API 기반 실제 안전성 검사 구현
        return {
            "is_safe": True,
            "security_reason": "통과",
            "messages": ["보안 검사 통과"],
        }


class TechAgent:
    """미션 실행 에이전트 -- BLIP/LLM 기반 미션 로직을 실행한다."""

    def execute_mission(self, state: CouncilState):
        """검증된 입력으로 미션을 실행한다.

        mission_type에 따라 run_mission1(장소) 또는 run_mission2(감성)을 호출.
        """
        print("[Tech Agent] 미션 실행 중...")
        user_input = state["user_input"]
        mission_type = user_input.get("mission_type")
        image_path = user_input.get("image_path")
        answer = user_input.get("answer")

        if mission_type == "photo":
            result = run_mission2(image_path, answer)
        else:
            result = run_mission1(image_path, answer)

        return {
            "mission_result": result,
            "messages": [f"미션 실행 완료: {result.get('success')}"],
        }


class DesignAgent:
    """응답 디자인 에이전트 -- 최종 사용자 응답을 생성한다."""

    def design_response(self, state: CouncilState):
        """미션 결과를 기반으로 사용자 친화적 응답을 생성한다.

        성공 시 축하 메시지, 실패 시 격려 메시지를 LLM으로 생성한다.
        """
        print("[Design Agent] 응답 디자인 중...")
        mission_result = state["mission_result"]

        if mission_result["success"]:
            msg = llm.invoke(
                [
                    SystemMessage(content="당신은 축하해주는 밝은 AI입니다."),
                    HumanMessage(
                        content=(
                            f"미션 성공! 쿠폰: {mission_result.get('coupon')} "
                            "내용을 바탕으로 축하 메시지 작성해줘."
                        )
                    ),
                ]
            ).content
        else:
            msg = mission_result.get("message", "다시 시도해보세요.")

        final_res = {
            "ui_theme": "confetti" if mission_result["success"] else "encouragement",
            "message": msg,
            "data": mission_result,
        }
        return {"final_response": final_res, "messages": ["응답 디자인 완료"]}


# 그래프 구성용 싱글톤 인스턴스
security_agent = SecurityAgent()
tech_agent = TechAgent()
design_agent = DesignAgent()
