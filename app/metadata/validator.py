from app.metadata.metadata import quick_photo_summary


def validate_metadata(image_path):
    """사진 메타데이터 유효성 검사를 실행한다.

    촬영일이 오늘인지, 파주출판단지 BBox 내부인지 확인하여
    둘 다 만족해야 True를 반환한다.
    """
    print("\n[STEP 1] 메타데이터 검증 중...")
    try:
        result = quick_photo_summary(image_path)
        if not result:
            print("⚠️ 메타데이터 검증 실패 (오늘 촬영 or 위치 조건 불만족)")
        return result
    except Exception as e:
        print(f"❌ 메타데이터 검증 실패: {e}")
        return False
