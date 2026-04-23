import os
import shutil

ASSETS_DIR = "data/assets"

# 폴더명 매핑 (한글 -> 영문 접두사)
FOLDER_MAP = {
    "나남출판사": "nanam",
    "네모탑": "nemotap",
    "로드킬 부엉이": "owl",
    "마법천자문 손오공": "sonogong",
    "시연사진": "demo",
    "웅진역사관": "woongjin",
    "지혜의 숲": "wisdom_forest",
    "지혜의숲 고양이": "wisdom_cat",
    "지혜의숲 입구 조각상": "wisdom_entrance",
    "지혜의숲 조각상": "wisdom_statue",
    "창틀 피노 키오": "pino_window",
    "창틀 피노키오": "pino_window", # 병합
    "피노지움 조각상": "pino_statue",
    "피노키오": "pino",
    "활돌이": "hwaldori",
    "활판 공방": "hwalpan",
    "활판공방 인쇄기": "hwalpan_press"
}

def rename_assets():
    for kr_folder, prefix in FOLDER_MAP.items():
        src_path = os.path.join(ASSETS_DIR, kr_folder)
        if not os.path.exists(src_path):
            continue
            
        # 대상 폴더 (병합 고려)
        dest_folder = os.path.join(ASSETS_DIR, kr_folder.replace(" ", ""))
        dest_path = os.path.join(ASSETS_DIR, dest_folder)
        
        # 파일 목록 가져오기
        files = [f for f in os.listdir(src_path) if os.path.isfile(os.path.join(src_path, f))]
        files.sort()
        
        for i, filename in enumerate(files, 1):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.jfif', '.webp']:
                continue
                
            new_name = f"{prefix}_{i:02d}{ext}"
            old_file_path = os.path.join(src_path, filename)
            new_file_path = os.path.join(src_path, new_name)
            
            # 임시 이름으로 변경 (충돌 방지)
            temp_name = f"temp_{new_name}"
            temp_path = os.path.join(src_path, temp_name)
            os.rename(old_file_path, temp_path)

        # 다시 한 번 돌면서 최종 이름으로 확정
        temp_files = [f for f in os.listdir(src_path) if f.startswith("temp_")]
        for f in temp_files:
            final_name = f.replace("temp_", "")
            os.rename(os.path.join(src_path, f), os.path.join(src_path, final_name))
            
    print("Asset renaming completed.")

if __name__ == "__main__":
    rename_assets()
