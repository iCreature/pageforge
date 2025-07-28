"""
Unit tests for pageforge.builder (Builder pattern, intermediate state).
"""
import pytest

from pageforge.core.builder import DocumentBuilder
from pageforge.core.models import DocumentData, ImageData, Section


def test_builder_creates_sections(sample_data_dict):
    builder = DocumentBuilder()
    # Only use valid DocumentData fields
    doc_fields = {k: v for k, v in sample_data_dict.items() if k in DocumentData.__dataclass_fields__}
    doc = DocumentData(**doc_fields)
    builder.set_title(doc.title)
    for section in doc.sections:
        builder.add_section(section)
    assert builder._title == doc.title
    # Compare as Section objects
    expected_sections = [s if isinstance(s, Section) else Section(**{k: v for k, v in s.items() if k in Section.__dataclass_fields__}) for s in doc.sections]
    assert builder._sections == expected_sections

    # Add sections from dict
    builder2 = DocumentBuilder()
    builder2.set_title("DictDoc")
    builder2.add_section({"type": "paragraph", "text": "From dict"})
    assert builder2._sections[0].text == "From dict"

    # Add meta
    builder2.set_meta({"foo": "bar"})
    assert builder2._meta["foo"] == "bar"

    # Bulk add
    builder2.add_sections([
        {"type": "list", "items": ["A"]},
        {"type": "header", "text": "H"}
    ])
    assert builder2._sections[-2].type == "list"

    # Unicode
    builder2.add_section({"type": "paragraph", "text": "Zulu: Sawubona"})
    assert "Zulu" in builder2._sections[-1].text

    # Invalid section
    with pytest.raises(Exception):
        builder2.add_section({"type": "diagram"})

def test_builder_adds_images(sample_data_dict):
    builder = DocumentBuilder()
    doc_fields = {k: v for k, v in sample_data_dict.items() if k in DocumentData.__dataclass_fields__}
    doc = DocumentData(**doc_fields)
    for img in doc.images:
        builder.add_image(img)
    # Compare as ImageData objects
    expected_images = [i if isinstance(i, ImageData) else ImageData(**{k: v for k, v in i.items() if k in ImageData.__dataclass_fields__}) for i in doc.images]
    assert builder._images == expected_images

    # Add image from dict
    builder.add_image({"name": "logo", "format": "PNG", "data": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"})
    assert builder._images[-1].name == "logo"

    # Invalid image type
    with pytest.raises(Exception):
        builder.add_image({"name": "bad", "data": b"", "format": "TIFF"})

def test_builder_handles_empty(empty_data_dict):
    builder = DocumentBuilder()
    doc = DocumentData(**empty_data_dict)
    builder.set_title(doc.title)
    assert builder._title == ""
    assert builder._sections == []
    assert builder._images == []

    # Partial build (missing title)
    builder2 = DocumentBuilder()
    builder2.add_section({"type": "paragraph", "text": "Hi"})
    with pytest.raises(Exception):
        builder2.build()

    # Reset/clear
    builder.set_title("X")
    builder.clear()
    assert builder._title is None
    assert builder._sections == []
    assert builder._images == []

    # Round-trip: builder -> DocumentData -> builder
    builder.set_title("RT")
    builder.add_section({"type": "paragraph", "text": "R"})
    builder.add_image({"name": "im", "data": b"1", "format": "PNG"})
    doc = builder.build()
    builder2 = DocumentBuilder.from_document(doc)
    assert builder2._title == "RT"
    assert builder2._sections[0].text == "R"
