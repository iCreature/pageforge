"""
Pytest fixtures for DocuForge tests.
"""
import io
import pytest
from unittest import mock
import sys
import os

# Ensure src/ is on sys.path for all test imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

@pytest.fixture
def sample_data_dict():
    return {
        "title": "Test Invoice",
        "sections": [
            {"type": "table", "rows": [["Item", "Qty", "Price"], ["Widget", 2, "$20"]]},
            {"type": "paragraph", "text": "Thank you for your business."}
        ],
        "images": [
            {"name": "logo", "data": b"fakeimagedata", "format": "PNG"}
        ],
        "footer": "Page 1 of 1"
    }

@pytest.fixture
def empty_data_dict():
    return {"title": "", "sections": [], "images": []}

@pytest.fixture
def huge_table_section():
    return {
        "type": "table",
        "rows": [[f"Col{i}" for i in range(100)]] + [[str(j) for j in range(100)] for j in range(200)]
    }

@pytest.fixture
def mock_engine():
    return mock.Mock()
