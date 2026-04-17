"""Qwen-VL 모델 스텁 (OpenRouter 연동).

OpenRouter 플랫폼을 통해 Qwen 멀티모달 모델을 호출한다.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


def _encode_image_base64(image_path: str) -> str:
    """이미지 파일을 Base64 인코딩 문자열로 변환한다.

    Args:
        image_path: 인코딩할 이미지 파일 경로.

    Returns:
        Base64 인코딩된 문자열.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def probe_with_qwen(
    mission_type: str,
    image_path: str,
    answer: str,
    prompt_bundle: dict[str, Any],
) -> dict[str, Any]:
    """OpenRouter를 경유하여 Qwen-VL 모델로 이미지를 분석한다.

    Args:
        mission_type: 미션 유형 ('location' | 'atmosphere').
        image_path: 분석할 이미지 파일 경로.
        answer: 미션 정답 키워드.
        prompt_bundle: 모델별 프롬프트 정보 딕셔너리.

    Returns:
        모델 투표 결과 딕셔너리 (model, score, label, reason).
    """
    if not settings.OPENROUTER_API_KEY:
        return {
            "model": "qwen",
            "score": 0.0,
            "label": "fail",
            "reason": "OPENROUTER_API_KEY가 설정되지 않아 Qwen-VL 호출을 건너뜁니다.",
        }

    try:
        logger.info(
            "[Agent: Evaluator / Model: Qwen] API 통신 시작 (Timeout: %ss, Retries: %s)",
            settings.API_TIMEOUT_SECONDS,
            settings.API_MAX_RETRIES,
        )
        llm = ChatOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            model=settings.QWEN_VL_MODEL_ID or "qwen/qwen3-vl-8b-instruct",
            temperature=0.1,
            max_tokens=300,
            timeout=settings.API_TIMEOUT_SECONDS,
            max_retries=settings.API_MAX_RETRIES,
        )

        base64_image = _encode_image_base64(image_path)
        qwen_prompt = prompt_bundle.get(
            "qwen_prompt", f"Does this image match the keyword: {answer}?"
        )

        system_instruction = (
            "You are an AI assistant specialized in analyzing images. "
            "You must respond ONLY with a valid JSON object. Do not include any markdown formatting like ```json. "
            "The JSON object must contain exactly three keys:\n"
            '1. "score": a float between 0.0 and 1.0 indicating your confidence.\n'
            '2. "label": either "match" or "mismatch".\n'
            '3. "reason": a short explanation of your reasoning based on the image.\n'
            f"Analyze the image according to this prompt: {qwen_prompt}"
        )

        msg = HumanMessage(
            content=[
                {"type": "text", "text": system_instruction},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
        )

        response = llm.invoke([msg])
        response_text = (
            response.content.replace("```json", "").replace("```", "").strip()
        )
        parsed = json.loads(response_text)

        return {
            "model": "qwen",
            "score": float(parsed.get("score", 0.0)),
            "label": parsed.get("label", "mismatch"),
            "reason": parsed.get("reason", "OpenRouter Qwen response parse failed."),
        }
    except Exception as exc:
        logger.error("[Qwen-VL Error] %s", exc)
        return {
            "model": "qwen",
            "score": 0.0,
            "label": "fail",
            "reason": f"OpenRouter API 호출 또는 파싱 오류: {exc}",
        }
