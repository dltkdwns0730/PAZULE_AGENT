from datetime import datetime, timezone
from app.services.mission_session_service import MissionSessionService


def test_reentry_prevention_logic():
    print("--- 재입장 방지 로직 테스트 시작 ---")
    svc = MissionSessionService()
    user_id = "test_user_reentry"
    mission_type = "location"

    # 1. 초기 상태 확인
    is_done = svc.is_mission_completed_today(user_id, mission_type)
    print(f"1. 초기 완료 상태 (기대: False): {is_done}")

    # 2. 미션 세션 생성 및 성공 기록
    session = svc.create_session(
        user_id=user_id,
        site_id="test",
        mission_type=mission_type,
        answer="정답",
        hint="힌트",
    )
    mission_id = session["mission_id"]
    svc.record_submission(mission_id, "hash123", {"success": True, "confidence": 0.95})
    print(f"2. 미션 성공 기록 완료: mission_id={mission_id}")

    # 3. 완료 상태 재확인
    is_done_after = svc.is_mission_completed_today(user_id, mission_type)
    print(f"3. 성공 후 완료 상태 (기대: True): {is_done_after}")

    if is_done_after:
        print(">>> 성공: 로직이 정상적으로 완료 상태를 감지함")
    else:
        print(">>> 실패: 로직이 완료 상태를 감지하지 못함")

        # 디버깅: 파일 내용 확인
        data = svc._read_all()
        relevant = [s for s in data.get("sessions", []) if s.get("user_id") == user_id]
        print(f"관련 세션 수: {len(relevant)}")
        if relevant:
            last = relevant[-1]
            print(f"최지막 세션 상태: {last.get('status')}")
            print(
                f"최지막 세션 성공 여부: {last.get('latest_judgment', {}).get('success')}"
            )
            print(f"최지막 세션 생성 시간: {last.get('created_at')}")
            print(
                f"시스템 오늘 시간 (UTC): {datetime.now(timezone.utc).date().isoformat()}"
            )


if __name__ == "__main__":
    test_reentry_prevention_logic()
