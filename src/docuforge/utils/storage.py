import os
from abc import ABC, abstractmethod


class StorageAdapter(ABC):
    @abstractmethod
    def save(self, data: bytes, key: str) -> str:
        pass

    @abstractmethod
    def load(self, key: str) -> bytes:
        pass

class LocalStorageAdapter(StorageAdapter):
    def save(self, data: bytes, key: str) -> str:
        os.makedirs(os.path.dirname(key), exist_ok=True)
        with open(key, 'wb') as f:
            f.write(data)
        return key

    def load(self, key: str) -> bytes:
        with open(key, 'rb') as f:
            return f.read()

class TigrisUploader:
    @classmethod
    def upload(cls, data: bytes, key: str) -> str:
        return cls._upload(data, key)

    @classmethod
    def _upload(cls, data: bytes, key: str) -> str:
        # Stub for tests; real impl would upload to Tigris and return the URL
        raise NotImplementedError("TigrisUploader._upload must be implemented")

class StorageRegistry:
    _registry: dict[str, StorageAdapter] = {}

    @classmethod
    def register(cls, name: str, adapter: StorageAdapter):
        cls._registry[name] = adapter

    @classmethod
    def get(cls, name: str) -> StorageAdapter:
        if name not in cls._registry:
            raise KeyError(f"Storage adapter '{name}' not registered")
        return cls._registry[name]
