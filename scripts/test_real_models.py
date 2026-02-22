import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
import sys
import asyncio
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 필수 환경변수 확인
REQUIRED_KEYS = ["OPENAI_API_KEY"] # 모델에 따라 다를 수 있음
missing_keys = [k for k in REQUIRED_KEYS if not os.getenv(k)]
if missing_keys:
    print(f"[경고] 다음 API Key가 .env 파일에 없습니다: {', '.join(missing_keys)}")
    print("실제 모델 추론 시 오류가 발생할 수 있습니다.\n")

from app.council.graph import pipeline_app
from app.services.answer_service import get_today_answers
from app.services.mission_session_service import mission_session_service
from app.models.model_registry import register_default_models
from app.prompts.registry import PromptRegistry
from app.core.config import settings
import traceback

def print_model_votes(votes):
    """모델별 투표 결과를 파싱해서 예쁘게 출력"""
    print(f"\n{'='*50}")
    print(f"[model_fanout] 실제 AI 모델 추론 결과 리포트")
    print(f"{'-'*50}")
    
    if not votes:
        print("  [ERROR] 모델 응답이 없습니다 (API Key 오류 또는 네트워크 문제)")
        return
        
    for idx, vote in enumerate(votes, 1):
        model_name = vote.get('model', 'Unknown')
        score = vote.get('score', 0)
        label = vote.get('label', 'N/A')
        reason = vote.get('reason', '')
        
        # 모델명 포맷팅 (글자수 맞춤)
        formatted_name = f"[{model_name.upper()}]".ljust(12)
        
        # 점수 기반 아이콘 매칭
        status_icon = "[PASS]" if score >= 0.7 else ("[WARN]" if score >= 0.4 else "[FAIL]")
        
        print(f"  {status_icon} {formatted_name} Score: {score:.2f} | Label: {label}")
        print(f"      -> Reason: {reason[:80]}...")
    print(f"{'='*50}\n")

def run_real_integration_test():
    try:
        # 1. 테스트용 이미지 경로 (본인 PC에 존재하는 사진으로 변경 필수)
        # TODO: 실제 테스트 시 이 경로를 반드시 유효한 이미지로 변경하세요!
        image_path = r"C:\Users\irubw\geminiProject\projects\active\PAZULE\front\src\assets\인트로1.jpg"
        
        if not os.path.exists(image_path):
            print(f"[에러] 테스트 이미지를 찾을 수 없습니다: {image_path}")
            print("코드를 수정하여 존재하는 이미지의 절대 경로를 입력해 주세요.")
            return

        user_id = "real_integration_test_user_01"
        site_id = "test-site-01"
        mission_type = "location"  # location 또는 atmosphere
        
        # 2. 정답 가져오기
        a1, a2, h1, h2 = get_today_answers()
        answer = a1 if mission_type == "location" else a2
        hint = h1 if mission_type == "location" else h2
        
        print(f"==================================================")
        print(f"PAZULE 실서버(DB/API) 통합 검증 테스트 시작")
        print(f"==================================================")
        print(f"[설정 정보]")
        print(f"- Target Answer : {answer}")
        print(f"- Image Path    : {image_path}")
        print(f"- Mission Type  : {mission_type}")
        print(f"- Target Models : ALL (ensemble)")
        print(f"--------------------------------------------------")

        # 3. DB 세션 생성 시도
        try:
            session = mission_session_service.create_session(
                user_id=user_id,
                site_id=site_id,
                mission_type=mission_type,
                answer=answer,
                hint=hint,
            )
            mission_id = session["mission_id"]
            print("[SUCCESS] DB 연동 성공 (세션 생성 완료)")
        except Exception as e:
            print(f"[ERROR] DB 연동 실패 (SQLite 쓰기 권한 또는 Schema 문제): {e}")
            return

        initial_state = {
            "request_context": {
                "mission_id": mission_id,
                "user_id": user_id,
                "site_id": site_id,
                "mission_type": mission_type,
                "image_path": image_path,
                "answer": answer,
                "model_selection": "ensemble",  # 모든 모델 프로브 호출
            },
            "artifacts": {},
            "errors": [],
            "control_flags": {},
            "messages": [],
        }

        # 4. 파이프라인 스트리밍
        print("\n[파이프라인 실행 중...] 모델 추론에 몇 초(또는 수십 초) 소요될 수 있습니다.")
        
        for s in pipeline_app.stream(initial_state):
            for node_name, state in s.items():
                artifacts = state.get("artifacts", {})
                
                # 시각적으로 분리
                print(f"\n[모듈 실행 완료] : {node_name}")
                
                if node_name == "validator":
                    print(f"  - Gate 통과 여부: {artifacts.get('gate_result', {}).get('passed')}")
                
                elif node_name == "router":
                    print(f"  - Route 결정: {artifacts.get('route_decision', {}).get('next_node')}")
                
                elif node_name == "evaluator":
                    # 모델 추론 결과는 특별히 이쁘게 출력
                    print_model_votes(artifacts.get('model_votes', []))
                    
                elif node_name == "aggregator":
                    ensemble = artifacts.get('ensemble_result', {})
                    print(f"  - 합산 방식: {ensemble.get('mission_type')} weights 적용")
                    print(f"  - 최종 병합 점수: {ensemble.get('merged_score')} / 통과기준 {ensemble.get('threshold')}")
                
                elif node_name == "judge":
                    judgment = artifacts.get('judgment', {})
                    print(f"  - 성공 판정: {judgment.get('success')} (사유: {judgment.get('reason')})")
                    
                elif node_name == "responder":
                    resp = state.get('final_response', {})
                    print(f"  - 최종 응답 테마: {resp.get('ui_theme')}")
                    print(f"  - 최종 유저 메시지: {resp.get('message')}")
                    
    except Exception as e:
        print(f"\n[치명적 에러] 실행 중 오류가 발생했습니다:")
        traceback.print_exc()

if __name__ == "__main__":
    # 필수 컴포넌트 레지스트리 초기화
    PromptRegistry.get_instance().load_all(settings.PROMPT_TEMPLATES_DIR)
    register_default_models()
    
    # LangGraph pipeline 실행
    run_real_integration_test()
