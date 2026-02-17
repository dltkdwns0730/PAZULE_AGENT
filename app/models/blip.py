import json
import os

import torch
from PIL import Image
from transformers import BlipForQuestionAnswering, BlipProcessor

from app.core.config import settings

# 디바이스 설정
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

MODEL_NAME = settings.BLIP_MODEL_ID
LANDMARK_QA_FILE = settings.LANDMARK_QA_PATH
DATA_DIR = settings.DATA_DIR

# 미션 성공 기준 (75% 이상 정답)
SUCCESS_THRESHOLD = 0.75


def load_model():
    """BLIP VQA 모델과 프로세서를 로드한다."""
    print(f"BLIP VQA 모델 로딩 중: '{MODEL_NAME}'...")
    try:
        processor = BlipProcessor.from_pretrained(MODEL_NAME)
        model = BlipForQuestionAnswering.from_pretrained(MODEL_NAME).to(DEVICE)
        print("BLIP VQA 모델 로드 완료.")
        return processor, model
    except Exception as e:
        print(f"BLIP 모델 로드 오류: {e}")
        return None, None


def load_landmark_qa():
    """랜드마크별 Q&A 데이터를 JSON 파일에서 로드한다."""
    fallback_file = os.path.join(DATA_DIR, "landmark_qa.json")

    try:
        with open(LANDMARK_QA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"랜드마크 Q&A 데이터 로드 완료: '{LANDMARK_QA_FILE}'")
            return data
    except FileNotFoundError:
        if os.path.exists(fallback_file):
            try:
                with open(fallback_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"폴백 Q&A 데이터 로드: '{fallback_file}'")
                    return data
            except Exception as e:
                print(f"폴백 파일 로드 실패: {e}")
        else:
            print(f"Q&A 파일 없음: '{LANDMARK_QA_FILE}' / '{fallback_file}'")
        return {}
    except json.JSONDecodeError:
        print(f"JSON 디코딩 실패: '{LANDMARK_QA_FILE}'")
        return {}


# 전역 모델/데이터 로드 (성능 최적화)
processor, model = load_model()
landmark_qa_data = load_landmark_qa()


def check_with_blip(user_image_path, landmark_name):
    """BLIP VQA로 사용자 이미지가 해당 랜드마크인지 검증한다.

    Args:
        user_image_path: 사용자가 업로드한 이미지 경로
        landmark_name: 오늘의 정답 랜드마크 이름

    Returns:
        (is_success, hint_payload) 튜플.
        is_success: 미션 성공 여부
        hint_payload: 오답 질문 목록 (LLM 힌트 생성용)
    """
    if not processor or not model:
        print("오류: BLIP 모델 미로드 상태")
        return False, []

    question_list = landmark_qa_data.get(landmark_name)
    if not question_list:
        print(f"경고: '{landmark_name}'에 대한 Q&A 데이터 없음")
        return False, []

    total_questions = len(question_list)
    if total_questions == 0:
        return False, []

    try:
        raw_image = Image.open(user_image_path).convert("RGB")
    except FileNotFoundError:
        print(f"오류: 이미지 파일 없음 '{user_image_path}'")
        return False, []
    except Exception as e:
        print(f"이미지 로드 오류: {e}")
        return False, []

    try:
        pixel_values = processor(
            images=raw_image, return_tensors="pt"
        ).pixel_values.to(DEVICE)
    except Exception as e:
        print(f"이미지 전처리 오류: {e}")
        return False, []

    correct_count = 0
    incorrect_questions_list = []

    print(f"VQA 실행 중: '{landmark_name}' ({total_questions}개 질문)...")

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
        except Exception as e:
            print(f"VQA 처리 오류 ('{question}'): {e}")
            incorrect_questions_list.append(
                {
                    "question": question,
                    "model_answer": "error",
                    "expected_answer": expected_answer,
                }
            )

    accuracy = correct_count / total_questions
    is_success = accuracy >= SUCCESS_THRESHOLD

    print(
        f"VQA 결과: {correct_count}/{total_questions} 정답 ({accuracy:.2%}). "
        f"성공: {is_success}"
    )

    if is_success:
        return True, []
    return False, incorrect_questions_list


def get_visual_context(user_image_path):
    """BLIP VQA로 이미지의 전반적인 분위기와 특징을 텍스트로 추출한다.

    감성 미션(미션2)에서 CLIP 대체용으로 사용한다.
    """
    if not processor or not model:
        return "모델 미로드 상태"

    try:
        raw_image = Image.open(user_image_path).convert("RGB")
        pixel_values = processor(
            images=raw_image, return_tensors="pt"
        ).pixel_values.to(DEVICE)
    except Exception as e:
        return f"이미지 로드 오류: {e}"

    # 분위기 파악을 위한 핵심 질문 리스트
    probes = [
        "What is the atmosphere of this picture?",
        "What is the dominant color?",
        "Is this picture bright or dark?",
        "How does this picture feel?",
        "What objects are in the picture?",
        "Is it natural or artificial?",
    ]

    context_parts = []
    print("BLIP으로 시각적 컨텍스트 추출 중...")

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
        except Exception as e:
            print(f"VQA 오류 ('{question}'): {e}")

    return "\n".join(context_parts)
