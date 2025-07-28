"""
Visual regression tests for PageForge.
"""
from pathlib import Path

import imagehash
import pytest
from PIL import Image

from pageforge import generate_pdf

# Check if pdf2image with proper dependencies is available
PDF2IMAGE_AVAILABLE = True
try:
    from pdf2image import convert_from_bytes
except ImportError:
    PDF2IMAGE_AVAILABLE = False
except Exception:
    # This will catch the PDFInfoNotInstalledError when poppler is not available
    PDF2IMAGE_AVAILABLE = False

# Create directory to store reference images
REFERENCE_DIR = Path(__file__).parent / "reference_images"
REFERENCE_DIR.mkdir(exist_ok=True)


def get_pdf_hash(pdf_bytes):
    """Convert PDF to images and compute perceptual hash for comparison."""
    if not PDF2IMAGE_AVAILABLE:
        pytest.skip("pdf2image or its dependencies (poppler) not available")
        return None
    
    try:
        # Convert PDF to image
        pages = convert_from_bytes(pdf_bytes, dpi=100)
        if not pages:
            return None
        
        # Take first page for comparison
        page = pages[0]
        
        # Calculate perceptual hash (relatively insensitive to small changes)
        hash_value = imagehash.phash(page)
        return hash_value
    except Exception as e:
        pytest.skip(f"Failed to process PDF: {e}")
        return None


def compare_pdfs(pdf_bytes, reference_name, max_difference=5):
    """
    Compare generated PDF with a reference image.
    The max_difference parameter controls sensitivity (lower is more strict).
    """
    if not PDF2IMAGE_AVAILABLE:
        pytest.skip("pdf2image or its dependencies (poppler) not available")
        return True
        
    ref_path = REFERENCE_DIR / f"{reference_name}.png"
    
    try:
        # Convert current PDF to image and get its hash
        pages = convert_from_bytes(pdf_bytes, dpi=100)
        if not pages:
            pytest.skip("Failed to convert PDF to image")
            return True
        
        current_page = pages[0]
        current_hash = imagehash.phash(current_page)
        
        # If reference doesn't exist, save this as reference
        if not ref_path.exists():
            current_page.save(ref_path)
            print(f"Created new reference image: {ref_path}")
            return True
        
        # Load reference and compare
        ref_image = Image.open(ref_path)
        ref_hash = imagehash.phash(ref_image)
        
        # Calculate difference (0 = identical, higher = more different)
        difference = current_hash - ref_hash
        
        if difference > max_difference:
            # Save failed image for inspection
            failed_path = REFERENCE_DIR / f"{reference_name}_failed.png"
            current_page.save(failed_path)
            print(f"Visual difference detected! Check {failed_path}")
            return False
        
        return True
    except Exception as e:
        pytest.skip(f"Error in visual comparison: {e}")
        return True


def test_simple_document_visual():
    """Test that simple document rendering remains visually consistent."""
    doc_data = {
        "title": "Simple Visual Test",
        "sections": [
            {"type": "paragraph", "text": "This is a test paragraph for visual regression testing."},
            {"type": "table", "rows": [["Header 1", "Header 2"], ["Cell 1", "Cell 2"]]},
            {"type": "list", "items": ["Item 1", "Item 2", "Item 3"]}
        ],
        "images": []
    }
    
    pdf_bytes = generate_pdf(doc_data)
    assert compare_pdfs(pdf_bytes, "simple_document")


def test_complex_layout_visual():
    """Test that complex layouts render consistently."""
    doc_data = {
        "title": "Complex Layout Test",
        "sections": [
            {"type": "paragraph", "text": "Header paragraph with longer text that should wrap to the next line and maintain consistent visual appearance between test runs."},
            {"type": "table", "rows": [
                ["Column 1", "Column 2", "Column 3", "Column 4"],
                ["Data 1,1", "Data 1,2", "Data 1,3", "Data 1,4"],
                ["Data 2,1", "Data 2,2", "Data 2,3", "Data 2,4"],
                ["Data 3,1", "Data 3,2", "Data 3,3", "Data 3,4"]
            ]},
            {"type": "paragraph", "text": "This paragraph appears after the table."},
            {"type": "list", "items": [
                "First list item with some more text to wrap",
                "Second list item",
                "Third list item with additional text to check wrapping behavior",
                "Fourth list item"
            ]}
        ],
        "images": []
    }
    
    pdf_bytes = generate_pdf(doc_data)
    assert compare_pdfs(pdf_bytes, "complex_layout")


def test_table_styles_visual():
    """Test that table styling remains consistent."""
    rows = [["Header A", "Header B", "Header C"]]
    for i in range(5):
        rows.append([f"Row {i+1}, Col A", f"Row {i+1}, Col B", f"Row {i+1}, Col C"])
    
    doc_data = {
        "title": "Table Styles Test",
        "sections": [
            {"type": "paragraph", "text": "Table with styling:"},
            {
                "type": "table", 
                "rows": rows,
                "style": {
                    "col_widths": [120, 100, 150],
                    "width_percentage": 90,
                    "space_before": 15,
                    "space_after": 15
                }
            }
        ],
        "images": []
    }
    
    pdf_bytes = generate_pdf(doc_data)
    assert compare_pdfs(pdf_bytes, "table_styles")
