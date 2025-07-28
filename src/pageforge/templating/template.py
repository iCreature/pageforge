# (Optional) Template interface for future extensibility
from abc import ABC, abstractmethod
from typing import Any


class Template(ABC):
    @abstractmethod
    def render(self, data: Any) -> str:
        pass
