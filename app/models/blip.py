"""BLIP model wrapper used by mission and orchestration paths."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Tuple

import torch
from PIL import Image
from transformers import BlipForQuestionAnswering, BlipProcessor

from app.core.config import settings
from app.models.adapter_utils import normalize_label

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = settings.BLIP_MODEL_ID
LANDMARK_QA_FILE = settings.LANDMARK_QA_PATH
DATA_DIR = settings.DATA_DIR
SUCCESS_THRESHOLD = 0.75


def load_model():
    """Caller: ?? ?? ???? ???
    Purpose: `load_model` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: None
    Note: ?? ?? ?? ???? ???"""
    print(f"Loading BLIP VQA model: {MODEL_NAME}")
    try:
        proc = BlipProcessor.from_pretrained(MODEL_NAME)
        mdl = BlipForQuestionAnswering.from_pretrained(MODEL_NAME).to(DEVICE)
        print("BLIP model loaded")
        return proc, mdl
    except Exception as exc:
        print(f"BLIP model load failed: {exc}")
        return None, None


def load_landmark_qa() -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `load_landmark_qa` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: None
    Note: ?? ?? ?? ???? ???"""
    fallback_file = os.path.join(DATA_DIR, "landmark_qa.json")
    try:
        with open(LANDMARK_QA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        if os.path.exists(fallback_file):
            with open(fallback_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {}
    except Exception:
        return {}


processor, model = load_model()
landmark_qa_data = load_landmark_qa()


def check_with_blip(user_image_path: str, landmark_name: str) -> Tuple[bool, List[Dict[str, str]]]:
    """Legacy mission API used by existing services."""
    if not processor or not model:
        return False, []

    question_list = landmark_qa_data.get(landmark_name) or []
    if not question_list:
        return False, []

    try:
        raw_image = Image.open(user_image_path).convert("RGB")
        pixel_values = processor(images=raw_image, return_tensors="pt").pixel_values.to(
            DEVICE
        )
    except Exception:
        return False, []

    correct_count = 0
    incorrect_questions_list: List[Dict[str, str]] = []

    for question, expected_answer in question_list:
        try:
            inputs = processor(text=question, return_tensors="pt").to(DEVICE)
            out = model.generate(
                pixel_values=pixel_values,
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=10,
            )
            model_answer = processor.decode(out[0], skip_special_tokens=True).strip().lower()
        except Exception:
            model_answer = "error"

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

    accuracy = correct_count / max(1, len(question_list))
    return accuracy >= SUCCESS_THRESHOLD, incorrect_questions_list


def get_visual_context(user_image_path: str) -> str:
    """Caller: ?? ?? ???? ???
    Purpose: `get_visual_context` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: user_image_path: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    if not processor or not model:
        return "model unavailable"

    try:
        raw_image = Image.open(user_image_path).convert("RGB")
        pixel_values = processor(images=raw_image, return_tensors="pt").pixel_values.to(
            DEVICE
        )
    except Exception as exc:
        return f"image load failed: {exc}"

    probes = [
        "What is the atmosphere of this picture?",
        "What is the dominant color?",
        "Is this picture bright or dark?",
        "How does this picture feel?",
        "What objects are in the picture?",
        "Is it natural or artificial?",
    ]
    context_parts = []

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
        except Exception:
            continue

    return "\n".join(context_parts)


def probe_with_blip_location(
    user_image_path: str, answer: str, prompt_bundle: Dict[str, Dict[str, str]] | None = None
) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `probe_with_blip_location` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: user_image_path: ???? ???? ??; answer: ???? ???? ??; prompt_bundle: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    start = time.perf_counter()
    is_success, failed_list = check_with_blip(user_image_path, answer)
    total = len(landmark_qa_data.get(answer, []))
    wrong = len(failed_list)
    score = 1.0 if is_success else max(0.0, (total - wrong) / total) if total else 0.0
    label = normalize_label(score, SUCCESS_THRESHOLD)

    return {
        "model": "blip",
        "mission_type": "location",
        "label": label,
        "score": score,
        "confidence": min(0.95, 0.55 + score * 0.4),
        "reason": "BLIP VQA landmark verification",
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        "success": True,
        "evidence": {
            "answer": answer,
            "failed_questions": failed_list[:5],
            "prompt": (prompt_bundle or {}).get("blip", {}),
        },
    }


def probe_with_blip_atmosphere(
    user_image_path: str, answer: str, prompt_bundle: Dict[str, Dict[str, str]] | None = None
) -> Dict[str, Any]:
    """Caller: ?? ?? ???? ???
    Purpose: `probe_with_blip_atmosphere` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: user_image_path: ???? ???? ??; answer: ???? ???? ??; prompt_bundle: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    start = time.perf_counter()
    context = get_visual_context(user_image_path)
    from app.models.llm import llm_service  # Local import to keep module import lighter.

    verification = llm_service.verify_mood(answer, context)
    score = 0.78 if verification.get("success") else 0.34
    label = normalize_label(score, 0.62)

    return {
        "model": "blip",
        "mission_type": "atmosphere",
        "label": label,
        "score": score,
        "confidence": min(0.92, 0.5 + score * 0.45),
        "reason": verification.get("reason", "BLIP context + LLM verification"),
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        "success": True,
        "evidence": {
            "answer": answer,
            "prompt": (prompt_bundle or {}).get("blip", {}),
            "context_excerpt": context[:320],
        },
    }
