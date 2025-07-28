"""
Unit tests for pageforge.models (dataclasses, validation, edge cases).
"""
import pytest

from pageforge.core import models


def test_documentdata_validation_cases():
    # Valid cases
    valid_cases = [
        {"title": "Invoice", "sections": [], "images": []},
        {"title": "", "sections": [], "images": []},
        {"title": "Report", "sections": [], "images": [], "meta": {"author": "LLM"}},
    ]
    for data in valid_cases:
        models.DocumentData(**data)
    # Invalid cases
    invalid_cases = [
        {"title": "Invoice", "sections": None, "images": []},
        {"title": "Invoice", "sections": [], "images": None},
    ]
    for data in invalid_cases:
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
    # Bullet list
    section = models.Section(type="list", items=["A", "B", "C"])
    assert section.items == ["A", "B", "C"]
    # Header/footer
    header = models.Section(type="header", text="Doc Title")
    footer = models.Section(type="footer", text="Page 1")
    assert header.text == "Doc Title"
    assert footer.text == "Page 1"
    # Unsupported section type
    with pytest.raises(ValueError):
        models.Section(type="diagram")
    # Unsupported image format
    with pytest.raises(ValueError):
        models.ImageData(name="bad", data=b"123", format="TIFF")
    # Empty image data
    with pytest.raises(ValueError):
        models.ImageData(name="empty", data=b"", format="PNG")
