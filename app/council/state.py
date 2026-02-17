import operator
from typing import Annotated, Any, Dict, List, TypedDict


class CouncilState(TypedDict):
    """Council 에이전트 간 공유 상태"""

    request_type: str  # "mission", "preview" 등
    user_input: Dict[str, Any]  # 이미지 경로, 텍스트 등

    # Security Agent 결과
    is_safe: bool
    security_reason: str

    # Tech Agent 결과
    mission_result: Dict[str, Any]

    # Design Agent 결과
    final_response: Dict[str, Any]

    # 메시지 히스토리
    messages: Annotated[List[str], operator.add]
