"""BLIP VQA 모델을 이용한 위치·분위기 미션 검증 모듈."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import torch
from PIL import Image
from transformers import BlipForQuestionAnswering, BlipProcessor

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── 디바이스 및 전역 설정 ──────────────────────────────────────────────────
DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME: str = settings.BLIP_MODEL_ID
LANDMARK_QA_FILE: str = settings.LANDMARK_QA_PATH
DATA_DIR: str = settings.DATA_DIR

# 미션 성공 기준 (75% 이상 정답)
SUCCESS_THRESHOLD: float = 0.75


def load_model() -> tuple[BlipProcessor | None, BlipForQuestionAnswering | None]:
    """BLIP VQA 모델과 프로세서를 로드한다.

    Returns:
        (processor, model) 튜플. 로드 실패 시 (None, None).
    """
    logger.info("BLIP VQA 모델 로딩 중: '%s'...", MODEL_NAME)
    try:
        processor = BlipProcessor.from_pretrained(MODEL_NAME)
        model = BlipForQuestionAnswering.from_pretrained(MODEL_NAME).to(DEVICE)
        logger.info("BLIP VQA 모델 로드 완료.")
        return processor, model
    except Exception as exc:
        logger.error("BLIP 모델 로드 오류: %s", exc)
        return None, None


def load_landmark_qa() -> dict[str, Any]:
    """랜드마크별 Q&A 데이터를 JSON 파일에서 로드한다.

    Returns:
        랜드마크명을 키로 하는 Q&A 딕셔너리. 로드 실패 시 빈 딕셔너리.
    """
    fallback_file = os.path.join(DATA_DIR, "landmark_qa.json")

    try:
        with open(LANDMARK_QA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info("랜드마크 Q&A 데이터 로드 완료: '%s'", LANDMARK_QA_FILE)
            return data
    except FileNotFoundError:
        if os.path.exists(fallback_file):
            try:
                with open(fallback_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info("폴백 Q&A 데이터 로드: '%s'", fallback_file)
                    return data
            except Exception as exc:
                logger.error("폴백 파일 로드 실패: %s", exc)
        else:
            logger.warning(
                "Q&A 파일 없음: '%s' / '%s'", LANDMARK_QA_FILE, fallback_file
            )
        return {}
    except json.JSONDecodeError:
        logger.error("JSON 디코딩 실패: '%s'", LANDMARK_QA_FILE)
        return {}


# ── 전역 모델/데이터 로드 (성능 최적화) ────────────────────────────────────
processor, model = load_model()
landmark_qa_data = load_landmark_qa()


def check_with_blip(
    user_image_path: str,
    landmark_name: str,
) -> tuple[bool, list[dict[str, str]]]:
    """BLIP VQA로 사용자 이미지가 해당 랜드마크인지 검증한다.

    Args:
        user_image_path: 사용자가 업로드한 이미지 경로.
        landmark_name: 오늘의 정답 랜드마크 이름.

    Returns:
        (is_success, hint_payload) 튜플.
        is_success: 미션 성공 여부 (정답률 ≥ SUCCESS_THRESHOLD).
        hint_payload: 오답 질문 목록 (LLM 힌트 생성용). 성공 시 [].
    """
    if not processor or not model:
        logger.error("BLIP 모델 미로드 상태")
        return False, []

    question_list = landmark_qa_data.get(landmark_name)
    if not question_list:
        logger.warning("'%s'에 대한 Q&A 데이터 없음", landmark_name)
        return False, []

    total_questions = len(question_list)
    if total_questions == 0:
        return False, []

    try:
        raw_image = Image.open(user_image_path).convert("RGB")
    except FileNotFoundError:
        logger.error("이미지 파일 없음: '%s'", user_image_path)
        return False, []
    except Exception as exc:
        logger.error("이미지 로드 오류: %s", exc)
        return False, []

    try:
        pixel_values = processor(images=raw_image, return_tensors="pt").pixel_values.to(
            DEVICE
        )
    except Exception as exc:
        logger.error("이미지 전처리 오류: %s", exc)
        return False, []

    correct_count = 0
    incorrect_questions_list: list[dict[str, str]] = []

    logger.info("VQA 실행 중: '%s' (%d개 질문)...", landmark_name, total_questions)

    for item in question_list:
        question, expected_answer = item[0], item[1]
        try:
            inputs = processor(text=question, return_tensors="pt").to(DEVICE)
            out = model.generate(
                pixel_values=pixel_values,
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=10,
            )
            model_answer = (
                processor.decode(out[0], skip_special_tokens=True).strip().lower()
            )
            if model_answer == expected_answer:
                correct_count += 1
            else:
                incorrect_questions_list.append(
                    {
                        "question": question,
                        "model_answer": model_answer,
                        "expected_answer": expected_answer,
                    }
                )
        except Exception as exc:
            logger.warning("VQA 처리 오류 ('%s'): %s", question, exc)
            incorrect_questions_list.append(
                {
                    "question": question,
                    "model_answer": "error",
                    "expected_answer": expected_answer,
                }
            )

    accuracy = correct_count / total_questions
    is_success = accuracy >= SUCCESS_THRESHOLD
    logger.info(
        "VQA 결과: %d/%d 정답 (%.2f%%). 성공: %s",
        correct_count,
        total_questions,
        accuracy * 100,
        is_success,
    )

    if is_success:
        return True, []
    return False, incorrect_questions_list


def get_visual_context(user_image_path: str) -> str:
    """BLIP VQA로 이미지의 전반적인 분위기와 특징을 텍스트로 추출한다.

    감성 미션(미션2)에서 CLIP 대체용으로 사용한다.

    Args:
        user_image_path: 분석할 이미지 파일 경로.

    Returns:
        질문별 BLIP 답변을 줄바꿈으로 연결한 컨텍스트 문자열.
        모델 미로드 또는 이미지 오류 시 에러 메시지 문자열.
    """
    if not processor or not model:
        return "모델 미로드 상태"

    try:
        raw_image = Image.open(user_image_path).convert("RGB")
        pixel_values = processor(images=raw_image, return_tensors="pt").pixel_values.to(
            DEVICE
        )
    except Exception as exc:
        return f"이미지 로드 오류: {exc}"

    probes = [
        "What is the atmosphere of this picture?",
        "What is the dominant color?",
        "Is this picture bright or dark?",
        "How does this picture feel?",
        "What objects are in the picture?",
        "Is it natural or artificial?",
    ]

    context_parts: list[str] = []
    logger.debug("BLIP으로 시각적 컨텍스트 추출 중...")

    for question in probes:
        try:
            inputs = processor(text=question, return_tensors="pt").to(DEVICE)
            out = model.generate(
                pixel_values=pixel_values,
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=20,
            )
            answer = processor.decode(out[0], skip_special_tokens=True).strip()
            context_parts.append(f"- {question} -> {answer}")
        except Exception as exc:
            logger.warning("VQA 오류 ('%s'): %s", question, exc)

    return "\n".join(context_parts)


def probe_with_blip_location(
    image_path: str,
    answer: str,
    prompt_bundle: dict[str, Any],
) -> dict[str, Any]:
    """BLIP VQA로 위치 미션을 검증한다 (파이프라인 인터페이스).

    Args:
        image_path: 이미지 파일 경로.
        answer: 미션 정답 랜드마크 이름.
        prompt_bundle: 프롬프트 번들 (현재 미사용, 인터페이스 통일 목적).

    Returns:
        모델 투표 결과 딕셔너리 {model, score, label, reason}.
    """
    is_success, _ = check_with_blip(image_path, answer)
    return {
        "model": "blip",
        "score": 1.0 if is_success else 0.0,
        "label": "match" if is_success else "mismatch",
        "reason": f"BLIP VQA location probe for '{answer}'",
    }


def probe_with_blip_atmosphere(
    image_path: str,
    answer: str,
    prompt_bundle: dict[str, Any],
) -> dict[str, Any]:
    """BLIP VQA로 분위기 미션을 검증한다 (파이프라인 인터페이스).

    Args:
        image_path: 이미지 파일 경로.
        answer: 미션 정답 분위기 키워드.
        prompt_bundle: 프롬프트 번들 (현재 미사용, 인터페이스 통일 목적).

    Returns:
        모델 투표 결과 딕셔너리 {model, score, label, reason}.
    """
    context = get_visual_context(image_path)
    keyword_lower = answer.lower()
    found = keyword_lower in context.lower()
    return {
        "model": "blip",
        "score": 0.85 if found else 0.2,
        "label": "match" if found else "mismatch",
        "reason": (
            f"BLIP atmosphere probe for '{answer}': "
            f"{'keyword found' if found else 'keyword not found'}"
        ),
    }
