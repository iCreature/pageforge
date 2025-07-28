"""
Unit tests for pageforge.storage (Tigris/S3 upload, URL return, mocks).
"""
import os
import tempfile
from unittest import mock

import pytest

from pageforge.utils.storage import (
    LocalStorageAdapter,
    StorageAdapter,
    StorageRegistry,
    TigrisUploader,
)


def test_upload_returns_url(monkeypatch):
    monkeypatch.setattr(TigrisUploader, "_upload", mock.Mock(return_value="https://fake.tigris/reports/test.pdf"))
    url = TigrisUploader.upload(b"pdfbytes", "reports/test.pdf")
    assert url.startswith("https://fake.tigris/")
    TigrisUploader._upload.assert_called_once()

# Local storage tests
def test_local_storage_save_and_load():
    adapter = LocalStorageAdapter()
    with tempfile.TemporaryDirectory() as tmpdir:
        key = os.path.join(tmpdir, "test.pdf")
        url = adapter.save(b"pdfbytes", key)
        assert os.path.exists(url)
        data = adapter.load(key)
        assert data == b"pdfbytes"

# Error handling
def test_local_storage_save_error():
    adapter = LocalStorageAdapter()
    with pytest.raises(OSError):
        adapter.save(b"bytes", "/bad/path/test.pdf")

# Adapter interface/registry
class DummyStorage(StorageAdapter):
    def save(self, data: bytes, key: str) -> str:
        return "dummy://" + key
    def load(self, key: str) -> bytes:
        return b"dummy"

def test_storage_interface_and_registry():
    dummy = DummyStorage()
    out = dummy.save(b"abc", "x")
    assert out.startswith("dummy://")
    assert dummy.load("x") == b"dummy"
    StorageRegistry.register("dummy", dummy)
    assert StorageRegistry.get("dummy") is dummy
    with pytest.raises(KeyError):
        StorageRegistry.get("none")

def test_upload_handles_failure(monkeypatch):
    # Mock the _upload method to fail with an exception
    mock_failure = mock.Mock(side_effect=RuntimeError("Upload failed"))
    monkeypatch.setattr(TigrisUploader, "_upload", mock_failure)
    
    with pytest.raises(RuntimeError):
        TigrisUploader.upload(b"pdfbytes", "bad.pdf")
