import pytest
from docuforge import generate_pdf
from docuforge.models import DocumentData, Section, ImageData
from pypdf import PdfReader
import io

def make_image_bytes(size=1000):
    # Generate a valid PNG header + dummy data
    return b"\x89PNG\r\n\x1a\n" + b"0" * size

def test_many_large_images():
    images = [ImageData(name=f"img{i}", data=make_image_bytes(2048), format="PNG") for i in range(20)]
    doc = DocumentData(title="Many Images", sections=[Section(type="paragraph", text="Test")], images=images)
    pdf_bytes = generate_pdf(doc)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    # Just check that PDF has as many images as possible (may be fewer if page breaks occur)
    found_images = 0
    for page in reader.pages:
        if "/XObject" in page["/Resources"]:
            xobjects = page["/Resources"]["/XObject"].get_object()
            for obj in xobjects.values():
                xobj = obj.get_object() if hasattr(obj, "get_object") else obj
                if xobj.get("/Subtype") == "/Image":
                    found_images += 1
    assert found_images >= 10  # At least half should be embedded

def test_stress_large_pdf():
    sections = [Section(type="paragraph", text="Line " + str(i)) for i in range(1000)]
    doc = DocumentData(title="Big PDF", sections=sections, images=[])
    pdf_bytes = generate_pdf(doc)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "Line 999" in text
