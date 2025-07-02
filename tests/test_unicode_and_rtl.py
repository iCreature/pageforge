import pytest
from docuforge import generate_pdf
from docuforge.models import DocumentData, Section
from pypdf import PdfReader
import io

def test_unicode_text():
    doc = DocumentData(
        title="ユニコードテスト",
        sections=[Section(type="paragraph", text="مرحبا بالعالم – Hello world – 你好，世界 – Здравствуйте, мир")],
        images=[]
    )
    pdf_bytes = generate_pdf(doc)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "مرحبا" in text and "Hello world" in text and "ユニコード" in text

def test_rtl_text():
    doc = DocumentData(
        title="RTL Test",
        sections=[Section(type="paragraph", text="שלום עולם"), Section(type="paragraph", text="مرحبا بالعالم")],
        images=[]
    )
    pdf_bytes = generate_pdf(doc)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "שלום עולם" in text and "مرحبا بالعالم" in text
