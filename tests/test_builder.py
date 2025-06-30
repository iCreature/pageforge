"""
Unit tests for docuforge.builder (Builder pattern, intermediate state).
"""
import pytest
from docuforge.builder import DocumentBuilder
from docuforge.models import DocumentData, Section, ImageData

def test_builder_creates_sections(sample_data_dict):
    builder = DocumentBuilder()
    doc = DocumentData(**sample_data_dict)
    builder.set_title(doc.title)
    for section in doc.sections:
        builder.add_section(section)
    assert builder._title == doc.title
    assert builder._sections == doc.sections

def test_builder_adds_images(sample_data_dict):
    builder = DocumentBuilder()
    doc = DocumentData(**sample_data_dict)
    for img in doc.images:
        builder.add_image(img)
    assert builder._images == doc.images

def test_builder_handles_empty(empty_data_dict):
    builder = DocumentBuilder()
    doc = DocumentData(**empty_data_dict)
    builder.set_title(doc.title)
    assert builder._title == ""
    assert builder._sections == []
    assert builder._images == []
