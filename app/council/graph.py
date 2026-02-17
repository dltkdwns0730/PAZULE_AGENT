from langgraph.graph import END, StateGraph

from app.council.agents import design_agent, security_agent, tech_agent
from app.council.state import CouncilState


def build_council_graph():
    """Security -> Tech -> Design 순서의 Council 그래프를 빌드한다.

    Security 검사 실패 시 바로 종료, 통과 시 Tech -> Design 순으로 진행.
    """
    workflow = StateGraph(CouncilState)

    # 노드 등록
    workflow.add_node("security", security_agent.check_safety)
    workflow.add_node("tech", tech_agent.execute_mission)
    workflow.add_node("design", design_agent.design_response)

    # 진입점
    workflow.set_entry_point("security")

    # Security 조건부 분기: 안전하면 tech, 아니면 종료
    def check_safe(state):
        return "tech" if state["is_safe"] else END

    workflow.add_conditional_edges("security", check_safe)
    workflow.add_edge("tech", "design")
    workflow.add_edge("design", END)

    return workflow.compile()


council_app = build_council_graph()
