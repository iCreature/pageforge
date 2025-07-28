"""PageForge high-level API functions for easy PDF generation."""

from pathlib import Path
from typing import BinaryIO, Optional, Union

from .core.builder import DocumentBuilder
from .core.models import DocumentData
from .engines.reportlab_engine import ReportLabEngine


def generate_pdf(document_data: Union[DocumentData, dict], **kwargs) -> bytes:
    """
    Generate a PDF document from document data.
    
    Args:
        document_data: Either a DocumentData object or a dictionary that can be converted to one
        **kwargs: Additional arguments to pass to the PDF engine
        
    Returns:
        bytes: PDF content as bytes
    """
    if isinstance(document_data, dict):
        document_data = DocumentData.from_dict(document_data)
    
    builder = DocumentBuilder(document_data)
    engine = ReportLabEngine(**kwargs)
    return builder.build(engine)


def generate_pdf_with_logo(
    document_data: Union[DocumentData, dict],
    logo_path: Union[str, Path, BinaryIO],
    logo_width: Optional[int] = None,
    logo_position: str = "top-center",
    **kwargs
) -> bytes:
    """
    Generate a PDF document with a logo.
    
    Args:
        document_data: Either a DocumentData object or a dictionary that can be converted to one
        logo_path: Path to logo image file or file-like object with read() method
        logo_width: Optional width to resize the logo (preserving aspect ratio)
        logo_position: Position of logo ("top-left", "top-center", "top-right", etc.)
        **kwargs: Additional arguments to pass to the PDF engine
        
    Returns:
        bytes: PDF content as bytes
    """
    if isinstance(document_data, dict):
        document_data = DocumentData.from_dict(document_data)
        
    # Prepare logo section
    if not hasattr(logo_path, 'read') and isinstance(logo_path, (str, Path)):
        with open(logo_path, 'rb') as f:
            logo_bytes = f.read()
    else:
        # Assume it's a file-like object
        logo_bytes = logo_path.read()
        
    # Create logo section at the specified position
    builder = DocumentBuilder(document_data)
    engine = ReportLabEngine(**kwargs)
    
    # Inject logo into the document
    engine.add_logo(logo_bytes, width=logo_width, position=logo_position)
    
    return builder.build(engine)
