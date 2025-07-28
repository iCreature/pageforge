"""
Pytest fixtures for PageForge tests.
"""
import os
import sys
from unittest import mock

import pytest

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
            {"name": "logo", "format": "PNG", "data": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"}
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
