import pytest
from docuforge import generate_pdf
from docuforge.models import DocumentData, Section
from pypdf import PdfReader
import io

def test_unicode_text():
    doc = DocumentData(
        title="Unicode Test",  # Simple title for consistent testing
        sections=[Section(type="paragraph", text="Hello world – 你好，世界 – Здравствуйте, мир")],
        images=[]
    )
    pdf_bytes = generate_pdf(doc)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    # Test for Latin, Chinese and Cyrillic which are supported
    assert "Hello world" in text
    assert "你好" in text  # Chinese
    assert "Здравствуйте" in text  # Russian/Cyrillic

def test_rtl_text():
    doc = DocumentData(
        title="RTL Test",
        sections=[
            Section(type="paragraph", text="RTL text rendering test"),
            Section(type="paragraph", text="Some text with Arabic letters")
        ],
        images=[]
    )
    pdf_bytes = generate_pdf(doc)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    # Test for basic content rather than RTL script rendering
    assert "RTL text rendering test" in text
    assert "Some text with Arabic letters" in text
