import os
import logging
import requests

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HintFlowDebug")

BASE_URL = "http://127.0.0.1:8080"


def debug_hint_flow():
    # 1. 의도적으로 실패할 미션 시작 (atmosphere)
    # 정답: '화사한' (현재 answer.json 기준 랜덤이지만, 고정하기 위해 특정 값 사용 시도)
    user_id = "debug_user"
    mission_type = "atmosphere"

    logger.info("1. Starting mission...")
    start_res = requests.post(
        f"{BASE_URL}/api/mission/start",
        json={"user_id": user_id, "mission_type": mission_type},
    )
    if not start_res.ok:
        logger.error(f"Failed to start mission: {start_res.text}")
        return

    start_data = start_res.json()
    mission_id = start_data["mission_id"]
    target_hint = start_data["hint"]
    logger.info(f"Mission started: {mission_id}, Hint: {target_hint}")

    # 2. 전혀 상관없는 이미지 제출 (검은색 배경 등)
    # 테스트를 위해 로컬에 아주 작은 검은색 이미지 생성
    from PIL import Image

    test_img_path = "debug_fail.jpg"
    Image.new("RGB", (100, 100), color="black").save(test_img_path)

    logger.info("2. Submitting failing image...")
    with open(test_img_path, "rb") as f:
        submit_res = requests.post(
            f"{BASE_URL}/api/mission/submit",
            data={"mission_id": mission_id},
            files={"image": f},
        )

    if not submit_res.ok:
        logger.error(f"Submission API error: {submit_res.text}")
    else:
        result = submit_res.json()
        logger.info(f"Submission Result: success={result.get('success')}")
        logger.info(f"Hint received: {result.get('hint')}")

        if not result.get("hint"):
            logger.error("CRITICAL: No hint returned in failure response!")
        else:
            logger.info("SUCCESS: Hint flow is working.")

    # 청소
    if os.path.exists(test_img_path):
        os.remove(test_img_path)


if __name__ == "__main__":
    # 서버가 떠 있는지 확인
    try:
        requests.get(BASE_URL, timeout=1)
        debug_hint_flow()
    except requests.RequestException:
        logger.error(
            "Server is not running on 8080. Please run 'python main.py' first."
        )
