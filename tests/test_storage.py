"""
Unit tests for docuforge.storage (Tigris/S3 upload, URL return, mocks).
"""
import pytest
from unittest import mock
from docuforge.storage import TigrisUploader

def test_upload_returns_url(monkeypatch):
    monkeypatch.setattr(TigrisUploader, "_upload", mock.Mock(return_value="https://fake.tigris/reports/test.pdf"))
    url = TigrisUploader.upload(b"pdfbytes", "reports/test.pdf")
    assert url.startswith("https://fake.tigris/")
    TigrisUploader._upload.assert_called_once()

def test_upload_handles_failure(monkeypatch):
    monkeypatch.setattr(TigrisUploader, "_upload", mock.Mock(side_effect=Exception("fail")))
    with pytest.raises(Exception):
        TigrisUploader.upload(b"pdfbytes", "bad.pdf")
