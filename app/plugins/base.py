"""Mission plugin abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class MissionPlugin(ABC):
    @property
    @abstractmethod
    def mission_type(self) -> str:
        ...

    @abstractmethod
    def execute(
        self, image_path: str, answer: str, prompt_bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        ...
