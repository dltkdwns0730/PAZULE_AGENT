"""프롬프트 미들웨어: 입력 sanitization 및 템플릿 변수 검증 모듈."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|above|all)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"<\|?(system|im_start|endoftext)\|?>", re.IGNORECASE),
    re.compile(r"```\s*(system|prompt)", re.IGNORECASE),
]

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def sanitize_input(text: str) -> str:
    """프롬프트 인젝션 패턴을 필터링한다.

    Args:
        text: 필터링할 입력 문자열.

    Returns:
        인젝션 패턴이 '[FILTERED]'로 대체된 문자열.
    """
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[FILTERED]", text)
    return text


def extract_placeholders(template: str) -> set[str]:
    """템플릿 문자열에서 {placeholder} 이름을 추출한다.

    Args:
        template: 플레이스홀더가 포함된 템플릿 문자열.

    Returns:
        플레이스홀더 이름 집합.
    """
    return set(_PLACEHOLDER_RE.findall(template))


def validate_template_vars(template: str, inputs: dict) -> None:
    """템플릿 플레이스홀더와 입력 키가 매칭되는지 검증한다.

    Args:
        template: 플레이스홀더가 포함된 템플릿 문자열.
        inputs: 렌더링에 사용할 입력 딕셔너리.

    Raises:
        ValueError: 필수 플레이스홀더에 대응하는 입력 키가 누락된 경우.
    """
    required = extract_placeholders(template)
    provided = set(inputs.keys())
    missing = required - provided
    if missing:
        raise ValueError(f"Missing template variables: {missing}")
