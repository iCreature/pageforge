"""
Unit tests for docuforge.storage (Tigris/S3 upload, URL return, mocks).
"""
import pytest
from unittest import mock
from docuforge.storage import TigrisUploader, StorageAdapter, LocalStorageAdapter, StorageRegistry
import tempfile, os

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
    with pytest.raises(Exception):
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
    monkeypatch.setattr(TigrisUploader, "_upload", mock.Mock(side_effect=Exception("fail")))
    with pytest.raises(Exception):
        TigrisUploader.upload(b"pdfbytes", "bad.pdf")
