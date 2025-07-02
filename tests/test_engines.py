"""
Unit tests for docuforge.engines (engine interface, calls, mocks).
"""
import pytest
from pypdf import PdfReader
from docuforge.engines.reportlab_engine import ReportLabEngine
from docuforge.engines.weasyprint_engine import WeasyPrintEngine
from docuforge.models import DocumentData
from docuforge.engines.engine_base import Engine, EngineRegistry

def test_reportlab_engine_calls(monkeypatch, sample_data_dict):
    engine = ReportLabEngine()
    monkeypatch.setattr(engine, "_render", mock.Mock(return_value=b"PDFDATA"))
    # Only use valid DocumentData fields
    doc_fields = {k: v for k, v in sample_data_dict.items() if k in DocumentData.__dataclass_fields__}
    doc = DocumentData(**doc_fields)
    pdf = engine.render(doc)
    engine._render.assert_called_once_with(doc)
    assert pdf == b"PDFDATA"
    assert isinstance(pdf, bytes)

    # Accept dict as input
    pdf2 = engine.render(sample_data_dict)
    assert isinstance(pdf2, bytes)

def test_weasyprint_engine_calls(monkeypatch, sample_data_dict):
    engine = WeasyPrintEngine()
    monkeypatch.setattr(engine, "_render", mock.Mock(return_value=b"PDFDATA2"))
    # Only use valid DocumentData fields
    doc_fields = {k: v for k, v in sample_data_dict.items() if k in DocumentData.__dataclass_fields__}
    doc = DocumentData(**doc_fields)
    pdf = engine.render(doc)
    engine._render.assert_called_once_with(doc)
    assert pdf == b"PDFDATA2"
    assert isinstance(pdf, bytes)

    # Accept dict as input
    pdf2 = engine.render(sample_data_dict)
    assert isinstance(pdf2, bytes)

def test_engine_invalid_data():
    engine = ReportLabEngine()
    with pytest.raises(Exception):
        engine.render(None)

    # Empty doc
    empty_doc = DocumentData(title="", sections=[], images=[])
    pdf = engine.render(empty_doc)
    assert isinstance(pdf, bytes)

    # Huge doc (simulate)
    big_doc = DocumentData(title="Big", sections=[{"type": "table", "rows": [[str(i)] * 10 for i in range(1000)]}], images=[])
    pdf = engine.render(big_doc)
    assert isinstance(pdf, bytes)

# Engine interface/ABC
class DummyEngine(Engine):
    def _render(self, doc):
        return b"dummy"

def test_engine_interface_and_registry(sample_data_dict):
    dummy = DummyEngine()
    out = dummy.render(sample_data_dict)
    assert out == b"dummy"
    assert isinstance(out, bytes)

    # Registry
    EngineRegistry.register("dummy", dummy)
    assert EngineRegistry.get("dummy") is dummy
    with pytest.raises(KeyError):
        EngineRegistry.get("doesnotexist")
