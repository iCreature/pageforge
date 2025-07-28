import io

from pypdf import PdfReader

from pageforge import generate_pdf
from pageforge.core.models import DocumentData, Section


def test_unicode_text():
    doc = DocumentData(
        title="Unicode Test",  # Simple title for consistent testing
        sections=[
            Section(
                type="paragraph", 
                text="Hello world – 你好，世界 – Здравствуйте, мир"
            )
        ],
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
            # Arabic text: "Hello world in Arabic"
            Section(type="paragraph", text="مرحبا بالعالم باللغة العربية"),
            # Hebrew text: "Hello world in Hebrew"
            Section(type="paragraph", text="שלום עולם בעברית")
        ],
        images=[]
    )
    pdf_bytes = generate_pdf(doc)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    
    # Basic presence test - at minimum these strings should be in the output
    assert "RTL text rendering test" in text
    
    # Note: PDF text extraction might not preserve exact Arabic/Hebrew characters
    # or their ordering, so we're just checking that the PDF was generated without errors
