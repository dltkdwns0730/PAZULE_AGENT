
import json
import os
from datetime import datetime, timezone, timedelta
import requests

BASE_URL = "http://127.0.0.1:5000" # 서버가 실행 중이라고 가정

def setup_mock_data():
    data_dir = "data"
    sessions_path = os.path.join(data_dir, "mission_sessions.json")
    coupons_path = os.path.join(data_dir, "coupons.json")
    
    today = datetime.now(timezone.utc).isoformat()
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    
    # Mock Sessions
    sessions = {
        "sessions": [
            {
                "mission_id": "today-success",
                "user_id": "guest",
                "mission_type": "location",
                "status": "coupon_issued",
                "created_at": today,
                "latest_judgment": {"success": True},
                "coupon_code": "TODAY-COUPON"
            },
            {
                "mission_id": "yesterday-success",
                "user_id": "guest",
                "mission_type": "atmosphere",
                "status": "coupon_issued",
                "created_at": yesterday,
                "latest_judgment": {"success": True},
                "coupon_code": "OLD-COUPON"
            }
        ]
    }
    
    # Mock Coupons
    coupons = {
        "coupons": [
            {
                "code": "TODAY-COUPON",
                "user_id": "guest",
                "mission_id": "today-success"
            },
            {
                "code": "OLD-COUPON",
                "user_id": "guest",
                "mission_id": "yesterday-success"
            }
        ]
    }
    
    with open(sessions_path, "w", encoding="utf-8") as f:
        json.dump(sessions, f)
    with open(coupons_path, "w", encoding="utf-8") as f:
        json.dump(coupons, f)
    print("Mock data setup complete.")

def verify_reset():
    # 1. Before Reset: Stats check
    res = requests.get(f"{BASE_URL}/api/user/stats?user_id=guest")
    stats = res.json()
    print(f"Before reset: total_attempts={stats['total_attempts']}, total_coupons={stats['total_coupons']}")
    
    # 2. Perform Reset
    print("Calling /api/user/reset...")
    res = requests.post(f"{BASE_URL}/api/user/reset", json={"user_id": "guest"})
    print(f"Reset result: {res.json()}")
    
    # 3. After Reset: Stats check (should be 1 attempt - the today's one, and 0 coupons)
    res = requests.get(f"{BASE_URL}/api/user/stats?user_id=guest")
    stats = res.json()
    print(f"After reset stats: total_attempts={stats['total_attempts']}, total_coupons={stats['total_coupons']}")
    
    # 4. Today's mission status check (should still be completed)
    res = requests.get(f"{BASE_URL}/get-today-hint?mission_type=location&user_id=guest")
    hint_data = res.json()
    print(f"Today's mission completed status: {hint_data.get('completed')}")
    
    # Assertions
    assert stats['total_coupons'] == 0, "Coupons should be cleared"
    # Note: Stats counts attempts based on what's in mission_sessions.json. 
    # Our reset logic keeps today's success, so total_attempts might be 1.
    assert hint_data.get('completed') == True, "Today's mission should still show as completed"
    print("Verification SUCCESSFUL!")

if __name__ == "__main__":
    # 이 스크립트를 실행하려면 Flask 서버가 별도의 프로세스로 떠 있어야 합니다.
    # 여기서는 로직만 테스트하기 위해 Mock 데이터를 직접 수정하고 서비스 클래스를 직접 호출하는 식으로 테스트할 수도 있습니다.
    pass
