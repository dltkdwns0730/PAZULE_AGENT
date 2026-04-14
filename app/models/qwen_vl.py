"""Qwen-VL 모델 스텁 (OpenRouter 연동).

OpenRouter 플랫폼을 통해 Qwen 멀티모달 모델을 호출합니다.
"""

from __future__ import annotations
import base64
import json
from typing import Any, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings


def _encode_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def probe_with_qwen(
    mission_type: str,
    image_path: str,
    answer: str,
    prompt_bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """OpenRouter를 경유하여 Qwen-VL 모델로 이미지를 분석한다."""
    if not settings.OPENROUTER_API_KEY:
        return {
            "model": "qwen",
            "score": 0.0,
            "label": "fail",
            "reason": "OPENROUTER_API_KEY가 설정되지 않아 Qwen-VL 호출을 건너뜁니다.",
        }

    try:
        print(
            f"  --> [Agent: Evaluator / Model: Qwen] API 통신 시작 (Timeout: {settings.API_TIMEOUT_SECONDS}s, Retries: {settings.API_MAX_RETRIES})"
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

        # JSON 포맷으로 출력하도록 명시적인 지시어 추가
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
    except Exception as e:
        print(f"[Qwen-VL Error] {e}")
        return {
            "model": "qwen",
            "score": 0.0,
            "label": "fail",
            "reason": f"OpenRouter API 호출 또는 파싱 오류: {e}",
        }
