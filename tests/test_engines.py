"""
Unit tests for docuforge.engines (engine interface, calls, mocks).
"""
import pytest
from unittest import mock
from docuforge.engines.reportlab_engine import ReportLabEngine
from docuforge.engines.weasyprint_engine import WeasyPrintEngine
from docuforge.models import DocumentData

def test_reportlab_engine_calls(monkeypatch, sample_data_dict):
    engine = ReportLabEngine()
    monkeypatch.setattr(engine, "_render", mock.Mock(return_value=b"PDFDATA"))
    doc = DocumentData(**sample_data_dict)
    pdf = engine.render(doc)
    engine._render.assert_called_once_with(doc)
    assert pdf == b"PDFDATA"

def test_weasyprint_engine_calls(monkeypatch, sample_data_dict):
    engine = WeasyPrintEngine()
    monkeypatch.setattr(engine, "_render", mock.Mock(return_value=b"PDFDATA2"))
    doc = DocumentData(**sample_data_dict)
    pdf = engine.render(doc)
    engine._render.assert_called_once_with(doc)
    assert pdf == b"PDFDATA2"

def test_engine_invalid_data():
    engine = ReportLabEngine()
    with pytest.raises(Exception):
        engine.render(None)
