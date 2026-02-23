"""Prompt middleware: input sanitization and template variable validation."""

from __future__ import annotations

import re
from typing import Set


_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|above|all)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"<\|?(system|im_start|endoftext)\|?>", re.IGNORECASE),
    re.compile(r"```\s*(system|prompt)", re.IGNORECASE),
]

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def sanitize_input(text: str) -> str:
    """프롬프트 인젝션 패턴을 필터링한다."""
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[FILTERED]", text)
    return text


def extract_placeholders(template: str) -> Set[str]:
    """템플릿 문자열에서 {placeholder} 이름을 추출한다."""
    return set(_PLACEHOLDER_RE.findall(template))


def validate_template_vars(template: str, inputs: dict) -> None:
    """템플릿 플레이스홀더와 입력 키가 매칭되는지 검증한다."""
    required = extract_placeholders(template)
    provided = set(inputs.keys())
    missing = required - provided
    if missing:
        raise ValueError(f"Missing template variables: {missing}")
