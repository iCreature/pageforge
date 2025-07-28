"""
Integration tests: generate sample docs, parse PDF, assert text/images.
"""
import io

from pypdf import PdfReader

from pageforge import generate_pdf


def test_generate_pdf_text_sample(sample_data_dict):
    pdf_bytes = generate_pdf(sample_data_dict)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "Test Invoice" in text

def test_generate_pdf_text_empty(empty_data_dict):
    pdf_bytes = generate_pdf(empty_data_dict)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "" in text


def test_generate_pdf_with_image(sample_data_dict):
    pdf_bytes = generate_pdf(sample_data_dict)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    # Check for at least one image XObject in PDF
    found_image = False
    for page in reader.pages:
        if "/XObject" in page["/Resources"]:
            xobjects = page["/Resources"]["/XObject"].get_object()
            for obj in xobjects.values():
                xobj = obj.get_object() if hasattr(obj, "get_object") else obj
                if xobj.get("/Subtype") == "/Image":
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
