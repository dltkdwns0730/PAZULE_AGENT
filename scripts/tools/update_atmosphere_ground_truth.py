"""
[Tool] Atmosphere Ground Truth Update Pipeline
--------------------------------------------------
목적: SigLIP2 모델을 사용하여 data/assets 내의 모든 이미지에 대해 5개 분위기 클러스터 점수를 측정하고,
      멀티라벨링된 Ground Truth 데이터(data/atmosphere_ground_truth_siglip2.json)를 자동 생성/갱신합니다.

환경:
- PYTHONPATH="." 설정 필요
- CUDA 지원 GPU 권장 (SigLIP2 로컬 추론용)
- PIL, numpy, tensorflow 등 필수 라이브러리 설치 필요

사용법:
$env:PYTHONPATH="."; python scripts/tools/update_atmosphere_ground_truth.py
"""

import os
import json
import logging
import numpy as np
from PIL import Image
from app.models.model_registry import register_default_models, ModelRegistry
from app.models.prompts import ATMOSPHERE_EN, build_prompt_bundle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AtmospherePipeline")

GROUND_TRUTH_PATH = "data/atmosphere_ground_truth_siglip2.json"
ASSETS_DIR = "data/assets"


def is_image_valid(img_path: str, threshold: float = 5.0) -> bool:
    """이미지가 단색인지 또는 정보량이 너무 적은지 확인한다.
    표준편차가 threshold 이하이면 유효하지 않은 것으로 판단.
    """
    try:
        with Image.open(img_path).convert("L") as img:  # 흑백으로 변환
            img_array = np.array(img)
            std_dev = np.std(img_array)
            return std_dev > threshold
    except Exception as e:
        logger.error(f"Error checking image validity: {e}")
        return False


def run_pipeline():
    # 1. 모델 준비
    register_default_models()
    registry = ModelRegistry.get_instance()
    siglip2 = registry.get("siglip2")

    # 2. 기존 데이터 로드 (무조건 새로 생성하도록 수정 가능)
    gt_data = {}

    # 3. 모든 에셋 스캔
    for folder_name in os.listdir(ASSETS_DIR):
        folder_path = os.path.join(ASSETS_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue

        images = [
            f
            for f in os.listdir(folder_path)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        for img_name in images:
            img_path = os.path.join(folder_path, img_name)
            relative_path = os.path.join(folder_name, img_name)

            logger.info(f"Processing image: {relative_path}")

            # 이미지 유효성 검사
            if not is_image_valid(img_path):
                logger.warning(
                    f"  -> Skipping invalid/monochromatic image: {relative_path}"
                )
                gt_data[relative_path] = {
                    "labels": ["무효함 (Monochromatic)"],
                    "scores": {k: 0.0 for k in ATMOSPHERE_EN.keys()},
                }
                continue

            scores = {}
            # 4개 클러스터에 대해 각각 점수 측정
            for kr_label in ATMOSPHERE_EN.keys():
                bundle = build_prompt_bundle("atmosphere", kr_label)
                res = siglip2.probe("atmosphere", img_path, kr_label, bundle)
                scores[kr_label] = res["score"]

            # 상위 1~2개 라벨 추출 (0.3 이상인 것만)
            multi_labels = [label for label, score in scores.items() if score >= 0.3]
            if not multi_labels:
                multi_labels = [max(scores, key=scores.get)]

            gt_data[relative_path] = {"labels": multi_labels, "scores": scores}

    # 4. 결과 저장
    with open(GROUND_TRUTH_PATH, "w", encoding="utf-8") as f:
        json.dump(gt_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Pipeline finished. Updated {GROUND_TRUTH_PATH}")


if __name__ == "__main__":
    run_pipeline()
