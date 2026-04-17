import os
import sys

from app.services.answer_service import get_today_answers
from app.legacy.mission_service import run_mission1

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
"""PAZULE 보물찾기 레거시 CLI 게임 루프.

웹 서버 없이 터미널에서 과거 미션 서비스 경로를 확인하는 진입점.
현재 운영 경로는 Flask API + LangGraph 파이프라인이며, 이 스크립트는
`app/legacy/mission_service.py` 호환 검증용으로만 유지된다.
"""


def print_header():
    """게임 시작 헤더를 출력한다."""
    print("=" * 60)
    print("  PAZULE 보물찾기 (CLI 버전)")
    print("=" * 60)
    print()


def print_footer():
    """게임 종료 푸터를 출력한다."""
    print()
    print("=" * 60)
    print("게임 종료. 다음에 또 만나요!")
    print("=" * 60)


def _init_registries():
    """프롬프트/모델/플러그인 레지스트리를 초기화한다."""
    from app.core.config import settings
    from app.prompts.registry import PromptRegistry
    from app.models.model_registry import register_default_models
    from app.legacy.plugins.registry import register_default_plugins

    PromptRegistry.get_instance().load_all(settings.PROMPT_TEMPLATES_DIR)
    register_default_models()
    register_default_plugins()


def main():
    """메인 게임 루프.

    1. 오늘의 정답 로드
    2. 사용자 이미지 경로 입력 대기
    3. LegacyMissionService로 검증
    4. 성공 시 쿠폰 발급, 실패 시 LLM 힌트 제공
    """
    _init_registries()
    print_header()

    # 1. 오늘의 정답 로드
    try:
        a1, a2, h1, h2 = get_today_answers()
        answer = a1
        initial_hint = h1

        print(f"[힌트] {initial_hint}")
        print()
        print("해당 장소를 찾아 사진을 찍고 파일 경로를 입력하세요.")
        print("'quit' 입력 시 종료합니다.")
        print()
    except Exception as e:
        print(f"정답 로드 실패: {e}")
        return

    # 2. 게임 루프
    attempt = 0
    while True:
        attempt += 1
        print("-" * 60)
        print(f"시도 #{attempt}")
        print("-" * 60)

        image_path = input("이미지 경로 (또는 'quit'): ").strip()

        if image_path.lower() == "quit":
            print("\n게임을 중단합니다.")
            break

        if not image_path:
            print("유효한 경로를 입력해주세요.\n")
            continue

        # 드래그 앤 드롭 시 따옴표 제거
        image_path = image_path.strip('"').strip("'")

        if not os.path.exists(image_path):
            print(f"파일을 찾을 수 없습니다: {image_path}")
            print("경로를 확인해주세요.\n")
            continue

        print()
        print("AI Council로 검증 중...")
        print()

        try:
            result = run_mission1(image_path, answer)
        except Exception as e:
            print(f"검증 중 오류 발생: {e}")
            import traceback

            traceback.print_exc()
            print("다시 시도해주세요.\n")
            continue

        # 결과 처리
        if result.get("success"):
            print("=" * 60)
            print("  정답입니다! 축하합니다!")
            print("=" * 60)
            print()

            coupon = result.get("coupon")
            print("쿠폰 발급 완료!")
            print(f"   {coupon}")
            print()
            print(f"정답: {answer}")
            print(f"총 시도 횟수: {attempt}")
            print()
            break
        else:
            print("=" * 60)
            print("  오답입니다!")
            print("=" * 60)
            print()

            hint = result.get("hint")
            message = result.get("message")

            print("AI 힌트:")
            print(f"   {hint}")
            print(f"   ({message})")
            print()
            print("다시 시도해보세요!\n")

    print_footer()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 게임이 중단되었습니다. (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n예상치 못한 오류: {e}")
        sys.exit(1)
