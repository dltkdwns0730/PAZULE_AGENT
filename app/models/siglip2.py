"""SigLIP2 모델 프로브 모듈.

실제 HuggingFace SigLIP2 모델 가중치를 로드하여 이미지-텍스트 유사도를 추론한다.
"""

from __future__ import annotations

import os
import traceback
from typing import Any, Dict

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel, GemmaTokenizerFast

from app.core.config import settings

# 디바이스 설정 (사용 가능한 경우 GPU, 아니면 CPU)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = settings.SIGLIP2_MODEL_ID

_image_processor = None
_tokenizer = None
_model = None


def _load_siglip2():
    """SigLIP2 기반 모델과 프로세서를 지연(lazy) 로드한다."""
    global _image_processor, _tokenizer, _model
    if _model is None:
        print(f"SigLIP2 모델 로딩 중: '{MODEL_NAME}' on {DEVICE}...")
        try:
            _image_processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
            _tokenizer = GemmaTokenizerFast.from_pretrained(MODEL_NAME)
            _model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
            _model.eval()
            print("SigLIP2 모델 로드 완료.")
        except Exception as e:
            print(f"SigLIP2 모델 로드 중 오류 발생: {e}")
            raise e


def probe_with_siglip2(
    mission_type: str,
    image_path: str,
    answer: str,
    prompt_bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """SigLIP2 모델로 이미지-텍스트 유사도를 측정한다.

    Args:
        mission_type: 미션 유형 ("location", "atmosphere" 등)
        image_path: 이미지 파일 경로
        answer: 미션 정답 키워드 (제출되어야 하는 목표)
        prompt_bundle: 프롬프트 번들

    Returns:
        모델 투표 결과 딕셔너리
    """
    try:
        _load_siglip2()
    except Exception as e:
        return {
            "model": "siglip2",
            "score": 0.0,
            "label": "mismatch",
            "reason": f"Model load failed: {e}",
        }

    try:
        raw_image = Image.open(image_path).convert("RGB")
    except Exception as e:
        return {
            "model": "siglip2",
            "score": 0.0,
            "label": "mismatch",
            "reason": f"Image load failed: {str(e)}",
        }

    # prompt_bundle의 영어 후보 텍스트 사용 (한국어 → 영어 변환 완료 상태)
    candidates = prompt_bundle.get("siglip2_candidates")
    if not candidates:
        if mission_type == "atmosphere":
            target_text = f"a photo with {answer} atmosphere"
        else:
            target_text = f"a photo of {answer}"
        candidates = [target_text]

    target_text = candidates[0]

    try:
        pixel_values = _image_processor(
            images=raw_image, return_tensors="pt"
        )["pixel_values"].to(DEVICE)
        input_ids = _tokenizer(
            candidates, return_tensors="pt", padding="max_length", max_length=64
        )["input_ids"].to(DEVICE)

        with torch.no_grad():
            outputs = _model(input_ids=input_ids, pixel_values=pixel_values)

        # SigLIP 특성상 softmax 대신 독립적인 sigmoid 함수가 사용됨
        logits_per_image = outputs.logits_per_image
        probs = torch.sigmoid(logits_per_image)  # shape: (1, 1)

        # numpy float로 변환
        score = float(probs[0][0].cpu().numpy())
    except Exception as e:
        print(f"[SigLIP2 Inference Error] {e}")
        traceback.print_exc()
        return {
            "model": "siglip2",
            "score": 0.0,
            "label": "mismatch",
            "reason": f"Inference failed: {e}",
        }

    # 스코어 기반으로 Pass/Fail 결정
    pass_threshold = (
        settings.LOCATION_PASS_THRESHOLD 
        if mission_type == "location" 
        else settings.ATMOSPHERE_PASS_THRESHOLD
    )
    label = "match" if score >= pass_threshold else "mismatch"

    return {
        "model": "siglip2",
        "score": score,
        "label": label,
        "reason": f"SigLIP2 prediction score for '{target_text}'",
    }
