"""프롬프트 레지스트리: AOP 데코레이터 기반 자동 프롬프트 주입 및 실행 로깅 모듈."""

from __future__ import annotations

import functools
import logging
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.prompts.loader import load_prompt_yaml
from app.prompts.middleware import sanitize_input, validate_template_vars

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    """선택된 프롬프트 variant 정보."""

    name: str
    version: str
    variant: str
    system: str
    user: str


@dataclass
class PromptRecord:
    """프롬프트 실행 기록."""

    prompt_name: str
    variant: str
    inputs: dict[str, Any]
    output: str | None = None
    latency_ms: float = 0.0


class PromptRegistry:
    """싱글턴 프롬프트 레지스트리: YAML 로드, variant 선택, 실행 기록."""

    _instance: PromptRegistry | None = None
    _initialized: bool = False

    def __new__(cls) -> PromptRegistry:
        """싱글턴 인스턴스를 반환한다."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """레지스트리를 초기화한다 (최초 1회만 실행)."""
        if self._initialized:
            return
        self._templates: dict[str, dict[str, Any]] = {}
        self._records: list[PromptRecord] = []
        self._initialized = True

    @classmethod
    def get_instance(cls) -> PromptRegistry:
        """싱글턴 인스턴스를 반환한다.

        Returns:
            PromptRegistry 싱글턴 인스턴스.
        """
        return cls()

    def load(self, path: str | Path) -> None:
        """단일 YAML 프롬프트 파일을 로드한다.

        Args:
            path: 로드할 YAML 프롬프트 파일 경로.
        """
        data = load_prompt_yaml(path)
        self._templates[data["name"]] = data

    def load_all(self, directory: str | Path) -> None:
        """디렉토리 내 모든 YAML 프롬프트 파일을 로드한다.

        Args:
            directory: YAML 파일이 있는 디렉토리 경로.
        """
        directory = Path(directory)
        if not directory.exists():
            return
        for yaml_path in sorted(directory.glob("*.yaml")):
            self.load(yaml_path)

    def get_template(self, name: str) -> dict[str, Any]:
        """이름으로 프롬프트 템플릿을 조회한다.

        Args:
            name: 프롬프트 템플릿 이름.

        Returns:
            프롬프트 템플릿 데이터 딕셔너리.

        Raises:
            KeyError: 해당 이름의 템플릿이 로드되지 않은 경우.
        """
        if name not in self._templates:
            raise KeyError(
                f"Prompt template '{name}' not found. Loaded: {list(self._templates.keys())}"
            )
        return self._templates[name]

    def select_variant(self, name: str) -> PromptVersion:
        """가중 랜덤으로 variant를 선택한다.

        Args:
            name: 프롬프트 템플릿 이름.

        Returns:
            선택된 PromptVersion 인스턴스.
        """
        template = self.get_template(name)
        variants = template["variants"]

        candidates = []
        weights = []
        for vname, vdata in variants.items():
            w = float(vdata.get("weight", 1.0))
            if w > 0:
                candidates.append((vname, vdata))
                weights.append(w)

        if not candidates:
            vdata = variants["default"]
            return PromptVersion(
                name=name,
                version=template["version"],
                variant="default",
                system=vdata["system"],
                user=vdata["user"],
            )

        chosen_name, chosen_data = random.choices(candidates, weights=weights, k=1)[0]
        return PromptVersion(
            name=name,
            version=template["version"],
            variant=chosen_name,
            system=chosen_data["system"],
            user=chosen_data["user"],
        )

    def render(self, name: str, inputs: dict[str, Any]) -> PromptVersion:
        """variant를 선택하고 입력값을 sanitize하여 렌더링한다.

        Args:
            name: 프롬프트 템플릿 이름.
            inputs: 렌더링에 사용할 입력 딕셔너리.

        Returns:
            렌더링된 PromptVersion 인스턴스.
        """
        pv = self.select_variant(name)

        sanitized = {k: sanitize_input(str(v)) for k, v in inputs.items()}

        validate_template_vars(pv.user, sanitized)

        pv.system = pv.system.format(**sanitized) if "{" in pv.system else pv.system
        pv.user = pv.user.format(**sanitized)

        return pv

    def record(self, rec: PromptRecord) -> None:
        """실행 기록을 저장한다.

        Args:
            rec: 저장할 PromptRecord 인스턴스.
        """
        self._records.append(rec)

    @property
    def records(self) -> list[PromptRecord]:
        """저장된 실행 기록 목록을 반환한다.

        Returns:
            PromptRecord 인스턴스 목록.
        """
        return list(self._records)


def with_prompt(prompt_name: str) -> Callable:
    """AOP 데코레이터: 함수에 PromptVersion을 자동 주입하고 실행 로깅한다.

    데코레이트된 함수는 keyword argument로 `prompt: PromptVersion`을 받는다.
    함수의 다른 kwargs는 프롬프트 템플릿 렌더링에 사용된다.

    Args:
        prompt_name: 주입할 프롬프트 템플릿 이름.

    Returns:
        데코레이터 함수.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            registry = PromptRegistry.get_instance()
            prompt_inputs = {k: v for k, v in kwargs.items() if k != "prompt"}

            start = time.time()
            prompt = registry.render(prompt_name, prompt_inputs)
            kwargs["prompt"] = prompt

            result = func(*args, **kwargs)

            latency_ms = (time.time() - start) * 1000
            registry.record(
                PromptRecord(
                    prompt_name=prompt_name,
                    variant=prompt.variant,
                    inputs=prompt_inputs,
                    output=str(result)[:500] if result else None,
                    latency_ms=latency_ms,
                )
            )
            return result

        return wrapper

    return decorator
