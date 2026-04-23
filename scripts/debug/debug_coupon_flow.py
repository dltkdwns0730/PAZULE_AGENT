from app.services.mission_session_service import MissionSessionService
from app.services.coupon_service import CouponService


def test_full_coupon_flow():
    # 1. 초기화
    print("--- 테스트 시작 ---")
    session_svc = MissionSessionService()
    coupon_svc = CouponService()
    user_id = "guest"

    # 2. 미션 세션 생성
    session = session_svc.create_session(
        user_id=user_id,
        site_id="test-site",
        mission_type="location",
        answer="지혜의 숲",
        hint="힌트",
    )
    mission_id = session["mission_id"]
    print(f"1. 세션 생성 완료: mission_id={mission_id}, user_id={session['user_id']}")

    # 3. 미션 성공 기록 시뮬레이션
    session_svc.record_submission(
        mission_id, "fake_hash", {"success": True, "confidence": 0.9}
    )
    print("2. 미션 성공 기록 완료")

    # 4. 쿠폰 발급 (현재 routes.py 로직 재현)
    reloaded_session = session_svc.get_session(mission_id)
    issued_coupon = coupon_svc.issue_coupon(
        mission_type="mission1",
        answer=reloaded_session["answer"],
        mission_id=mission_id,
        user_id=reloaded_session.get("user_id", "guest"),
    )
    print(
        f"3. 쿠폰 발급 완료: code={issued_coupon['code']}, user_id={issued_coupon.get('user_id')}"
    )

    # 5. 지갑 조회 (현재 routes.py get_user_coupons 로직 재현)
    user_coupons = coupon_svc.get_user_coupons(user_id)
    print(f"4. 지갑 조회 결과: {len(user_coupons)}개의 쿠폰 발견")

    found = any(c["code"] == issued_coupon["code"] for c in user_coupons)
    if found:
        print(">>> 성공: 발급된 쿠폰이 지갑에서 확인됨")
    else:
        print(">>> 실패: 발급된 쿠폰이 지갑에서 누락됨")

        # 상세 분석
        all_coupons = coupon_svc._read_all().get("coupons", [])
        print(f"전체 쿠폰 수: {len(all_coupons)}")
        for c in all_coupons:
            if c["mission_id"] == mission_id:
                print(f"대상 쿠폰 상세: {c}")


if __name__ == "__main__":
    test_full_coupon_flow()
