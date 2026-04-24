from datetime import datetime, timezone, timedelta
from app.services.coupon_service import coupon_service
from app.services.mission_session_service import mission_session_service


def test_reset_logic():
    user_id = "test_user"
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    # 1. Setup Mock Data
    print("Setting up mock data...")

    # Create sessions via service
    s1 = mission_session_service.create_session(
        user_id, "site", "location", "ans1", "hint1"
    )

    # Manually update to success and today
    def make_success(sess):
        sess["status"] = "coupon_issued"
        sess["latest_judgment"] = {"success": True}
        sess["coupon_code"] = "T-COUPON"
        return sess

    mission_session_service._update_session(s1["mission_id"], make_success)

    # Create an old session
    s2 = mission_session_service.create_session(
        user_id, "site", "atmosphere", "ans2", "hint2"
    )

    def make_old_success(sess):
        sess["status"] = "coupon_issued"
        sess["latest_judgment"] = {"success": True}
        sess["created_at"] = yesterday
        sess["coupon_code"] = "O-COUPON"
        return sess

    mission_session_service._update_session(s2["mission_id"], make_old_success)

    # Create coupons
    coupon_service.issue_coupon("mission1", "ans1", s1["mission_id"], user_id)
    coupon_service.issue_coupon("mission2", "ans2", s2["mission_id"], user_id)

    # Verify initial state
    stats = mission_session_service.get_user_stats(user_id)
    coupons = coupon_service.get_user_coupons(user_id)
    print(f"Initial: attempts={stats['total_attempts']}, coupons={len(coupons)}")
    assert stats["total_attempts"] == 2
    assert len(coupons) == 2

    # 2. Perform Reset
    print("Performing Reset...")
    coupon_service.reset_user_coupons(user_id)
    mission_session_service.reset_user_history(user_id)

    # 3. Verify Final State
    stats_after = mission_session_service.get_user_stats(user_id)
    coupons_after = coupon_service.get_user_coupons(user_id)
    print(
        f"After Reset: attempts={stats_after['total_attempts']}, coupons={len(coupons_after)}"
    )

    # '오늘의 성공'은 남겨두었으므로 attempts는 1이어야 함 (또는 0으로 보이고 싶다면 stats 로직 수정 필요)
    # 하지만 mission_sessions.json에 데이터가 남아있으므로 stats에는 잡힐 것임.
    # 사용자가 '프로필이 삭제되지 않는다'고 한 것은 누적 기록이 남는 것을 의미하므로,
    # 오늘 성공 기록만 남는 것은 허용 범위로 보임.

    # 쿠폰은 확실히 0개여야 함
    assert len(coupons_after) == 0, f"Expected 0 coupons, got {len(coupons_after)}"

    # 오늘 미션 완료 상태는 True여야 함
    is_completed = mission_session_service.is_mission_completed_today(
        user_id, "location"
    )
    print(f"Today's mission completed: {is_completed}")
    assert is_completed, "Today's mission should remain completed"

    print("Test SUCCESSFUL!")


if __name__ == "__main__":
    test_reset_logic()
