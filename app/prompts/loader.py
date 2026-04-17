"""YAML 프롬프트 템플릿 로더."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_REQUIRED_KEYS = {"name", "version", "variants"}


def load_prompt_yaml(path: str | Path) -> dict[str, Any]:
    """YAML 프롬프트 파일을 파싱하고 필수 키를 검증한다.

    Args:
        path: YAML 프롬프트 파일 경로.

    Returns:
        파싱된 프롬프트 데이터 딕셔너리.

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때.
        ValueError: 포맷이 잘못되었거나 필수 키가 누락된 경우.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid prompt template format: {path}")

    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"Missing required keys {missing} in {path}")

    variants = data.get("variants", {})
    if "default" not in variants:
        raise ValueError(f"Missing 'default' variant in {path}")

    for variant_name, variant in variants.items():
        if "system" not in variant or "user" not in variant:
            raise ValueError(
                f"Variant '{variant_name}' must have 'system' and 'user' keys in {path}"
            )

    return data
