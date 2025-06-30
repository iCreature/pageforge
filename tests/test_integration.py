"""
Integration tests: generate sample docs, parse PDF, assert text/images.
"""
import io
import pytest
from docuforge import generate_pdf
from PyPDF2 import PdfReader

@pytest.mark.parametrize("data_dict,expect_text", [
    (pytest.lazy_fixture("sample_data_dict"), "Test Invoice"),
    (pytest.lazy_fixture("empty_data_dict"), ""),
])
def test_generate_pdf_text(data_dict, expect_text):
    pdf_bytes = generate_pdf(data_dict)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert expect_text in text


def test_generate_pdf_with_image(sample_data_dict):
    pdf_bytes = generate_pdf(sample_data_dict)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    # Check for at least one image XObject in PDF
    found_image = False
    for page in reader.pages:
        if "/XObject" in page["/Resources"]:
            xobjects = page["/Resources"]["/XObject"].get_object()
            for obj in xobjects.values():
                if obj.get("/Subtype") == "/Image":
                    found_image = True
    assert found_image


def test_generate_pdf_edge_cases(empty_data_dict, huge_table_section):
    data_dict = empty_data_dict.copy()
    data_dict["sections"] = [huge_table_section]
    pdf_bytes = generate_pdf(data_dict)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "Col0" in text
    assert len(reader.pages) >= 1
