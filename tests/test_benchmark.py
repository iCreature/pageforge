"""
Performance benchmark tests for PageForge.
"""
import random
import string

import pytest

from pageforge import generate_pdf


def create_test_document(paragraph_count=10, table_size=(5, 5), list_items=5):
    """Create a test document with variable content for benchmarking."""
    sections = []
    
    # Add paragraphs
    for _ in range(paragraph_count):
        text = ' '.join(''.join(random.choices(string.ascii_letters + ' ', k=10)) for _ in range(20))
        sections.append({"type": "paragraph", "text": text})
    
    # Add a table
    rows = []
    rows.append([f"Header {i}" for i in range(table_size[1])])
    for r in range(table_size[0] - 1):
        rows.append([f"Cell {r},{c}" for c in range(table_size[1])])
    sections.append({"type": "table", "rows": rows})
    
    # Add a list
    items = [f"List item {i}" for i in range(list_items)]
    sections.append({"type": "list", "items": items})
    
    return {"title": "Benchmark Document", "sections": sections, "images": []}


@pytest.mark.benchmark(
    group="pdf-generation",
    min_rounds=5,
    max_time=2.0,
    min_time=0.1,
    warmup=False
)
def test_benchmark_small_document(benchmark):
    """Benchmark generating a small document."""
    doc_data = create_test_document(paragraph_count=5, table_size=(3, 3), list_items=3)
    pdf_bytes = benchmark(generate_pdf, doc_data)
    assert len(pdf_bytes) > 0


@pytest.mark.benchmark(
    group="pdf-generation",
    min_rounds=5,
    max_time=5.0,
    min_time=0.1,
    warmup=False
)
def test_benchmark_medium_document(benchmark):
    """Benchmark generating a medium-sized document."""
    doc_data = create_test_document(paragraph_count=20, table_size=(10, 5), list_items=10)
    pdf_bytes = benchmark(generate_pdf, doc_data)
    assert len(pdf_bytes) > 0


@pytest.mark.benchmark(
    group="pdf-generation",
    min_rounds=3,
    max_time=10.0,
    min_time=0.1,
    warmup=False
)
def test_benchmark_large_document(benchmark):
    """Benchmark generating a large document."""
    doc_data = create_test_document(paragraph_count=50, table_size=(20, 10), list_items=20)
    pdf_bytes = benchmark(generate_pdf, doc_data)
    assert len(pdf_bytes) > 0


@pytest.mark.benchmark(
    group="table-rendering",
    min_rounds=3,
    max_time=5.0,
    min_time=0.1,
    warmup=False
)
def test_benchmark_table_rendering(benchmark):
    """Benchmark table rendering specifically."""
    rows = [["Header " + str(i) for i in range(10)]]
    rows.extend([[f"Cell {r},{c}" for c in range(10)] for r in range(30)])
    doc_data = {"title": "Table Benchmark", "sections": [{"type": "table", "rows": rows}], "images": []}
    pdf_bytes = benchmark(generate_pdf, doc_data)
    assert len(pdf_bytes) > 0
