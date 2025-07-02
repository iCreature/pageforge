import pytest
from docuforge import generate_pdf
from docuforge.models import DocumentData, Section

def test_missing_section_type():
    doc = {
        "title": "Missing Type",
        "sections": [{"text": "No type field"}],
        "images": []
    }
    with pytest.raises(Exception):
        generate_pdf(doc)

def test_invalid_image_format():
    doc = {
        "title": "Invalid Image",
        "sections": [],
        "images": [{"name": "bad", "data": b"123", "format": "TIFF"}]
    }
    with pytest.raises(Exception):
        generate_pdf(doc)
