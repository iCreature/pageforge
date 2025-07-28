import pytest

from pageforge import generate_pdf


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
