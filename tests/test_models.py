"""
Unit tests for docuforge.models (dataclasses, validation, edge cases).
"""
import pytest
from docuforge import models

@pytest.mark.parametrize("data,valid", [
    ({"title": "Invoice", "sections": [], "images": []}, True),
    ({"title": "", "sections": [], "images": []}, True),
    ({"title": "Invoice", "sections": None, "images": []}, False),
    ({"title": "Invoice", "sections": [], "images": None}, False),
])
def test_documentdata_validation(data, valid):
    if valid:
        models.DocumentData(**data)
    else:
        with pytest.raises(Exception):
            models.DocumentData(**data)

def test_section_edge_cases():
    # Zero items
    section = models.Section(type="table", rows=[])
    assert section.rows == []
    # Huge tables
    rows = [[str(i) for i in range(100)]] * 200
    section = models.Section(type="table", rows=rows)
    assert len(section.rows) == 200
    # Missing optional fields
    section = models.Section(type="paragraph", text="Hello")
    assert hasattr(section, "text")
    # Unsupported image format
    with pytest.raises(ValueError):
        models.ImageData(name="bad", data=b"123", format="TIFF")
