from abc import ABC, abstractmethod
from typing import Any, Dict
from ..models import DocumentData

class Engine(ABC):
    """
    Abstract base class for all PDF engines.
    """
    @abstractmethod
    def _render(self, doc: DocumentData) -> bytes:
        pass

    def render(self, doc_or_dict: Any) -> bytes:
        if isinstance(doc_or_dict, dict):
            doc = DocumentData(**{k: v for k, v in doc_or_dict.items() if k in DocumentData.__dataclass_fields__})
        elif isinstance(doc_or_dict, DocumentData):
            doc = doc_or_dict
        else:
            raise TypeError("Input must be DocumentData or dict")
        out = self._render(doc)
        if not isinstance(out, bytes):
            raise TypeError("Engine must return bytes")
        return out

class EngineRegistry:
    _registry: Dict[str, Engine] = {}

    @classmethod
    def register(cls, name: str, engine: Engine):
        cls._registry[name] = engine

    @classmethod
    def get(cls, name: str) -> Engine:
        if name not in cls._registry:
            raise KeyError(f"Engine '{name}' not registered")
        return cls._registry[name]
