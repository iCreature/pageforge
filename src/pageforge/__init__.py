"""PageForge: Flexible, extensible PDF/document generation library for LLM & programmatic pipelines."""

from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("pageforge")
except ImportError:
    # Package is not installed
    __version__ = "0.0.0.dev0"

import logging
import os
from typing import Any, Dict, List, Optional, Union

# Set up package-level logger
logger = logging.getLogger("pageforge")

# Import all public API modules and components
# Convenience functions for the public API
from .api import generate_pdf, generate_pdf_with_logo
from .core.builder import DocumentBuilder
from .core.exceptions import (
    ConfigurationError,
    PageForgeError,
    FontError,
    ImageError,
    RenderingError,
    ResourceError,
    SectionError,
    ValidationError,
)
from .core.models import DocumentData, ImageData, Section
from .engines.reportlab_engine import ReportLabEngine

# Setup logging only if an environment variable is explicitly set
from .utils.logging_config import TRACE_ID, get_logger, init_logging

if os.environ.get('PAGEFORGE_CONFIGURE_LOGGING', 'false').lower() == 'true':
    log_file = os.environ.get('PAGEFORGE_LOG_FILE', None)
    init_logging(log_file=log_file)

__all__ = [
    # Core models
    'DocumentData', 'Section', 'ImageData',
    # Builders and engines
    'DocumentBuilder', 'ReportLabEngine',
    # Exceptions
    'PageForgeError', 'ValidationError', 'RenderingError',
    'ResourceError', 'ImageError', 'FontError', 'SectionError', 'ConfigurationError',
    # Public API functions
    'generate_pdf', 'generate_pdf_with_logo',
    # Utility functions
    'get_logger', 'TRACE_ID'
]

# Create package-level logger
logger = get_logger(__name__, {'trace_id': TRACE_ID})
logger.info(f"PageForge initialized with trace ID: {TRACE_ID}")

def generate_pdf(data: Union[dict[str, Any], DocumentData], engine: str = "reportlab") -> bytes:
    """
    Public API: Generate PDF bytes from structured data (dict or DocumentData).
    
    This is the main entry point for generating PDFs with PageForge. It accepts either
    a dictionary with document fields or a pre-configured DocumentData object.
    
    Args:
        data: Input data as dict or DocumentData object. If a dict is provided,
              it must contain at least a 'title' field, and optionally 'sections',
              'images', and 'meta' fields that match the DocumentData structure.
        engine: Name of the rendering engine to use (default: "reportlab").
              Currently only the ReportLab engine is fully implemented.
        
    Returns:
        PDF document as bytes that can be written to a file or served via HTTP.
        
    Raises:
        ValidationError: If document structure is invalid or data is improperly formatted.
        ConfigurationError: If the specified engine is not supported.
        RenderingError: If the rendering process fails.
        ImageError: If there are issues with image processing or embedding.
        SectionError: If there are issues with section content or processing.
        ResourceError: If there are issues with fonts or other resources.
        PageForgeError: Base exception for any other errors in the PDF generation process.
        
    Example:
        >>> from pageforge import generate_pdf
        >>> from pageforge.core.models import Section
        >>> doc_data = {"title": "My Document", "sections": [Section(type="paragraph", text="Hello world")]}
        >>> pdf_bytes = generate_pdf(doc_data)
        >>> with open("output.pdf", "wb") as f:
        >>>     f.write(pdf_bytes)
    """
    logger.info(f"Generating PDF using {engine} engine", context={'document_type': type(data).__name__})
    
    try:
        if isinstance(data, dict):
            logger.debug("Converting dictionary to DocumentData")
            # Filter out unknown keys for DocumentData
            doc_fields = {k: v for k, v in data.items() if k in DocumentData.__dataclass_fields__}
            doc = DocumentData(**doc_fields)
            logger.debug(f"Document title: {getattr(doc, 'title', 'Untitled')}")
        elif isinstance(data, DocumentData):
            logger.debug("Using provided DocumentData")
            doc = data
            logger.debug(f"Document title: {getattr(doc, 'title', 'Untitled')}")
        else:
            logger.error(f"Invalid input type: {type(data).__name__}")
            raise ValidationError(
                message="Invalid input data type",
                field="data",
                value=type(data).__name__,
                expected="dict or DocumentData"
            )
            
        # For now, only support ReportLab
        engine_obj = ReportLabEngine()
        logger.info(f"Rendering document with {len(getattr(doc, 'sections', []))} sections and {len(getattr(doc, 'images', []))} images")
        result = engine_obj.render(doc)
        logger.info(f"PDF generation complete, size: {len(result)} bytes")
        return result
    except Exception as e:
        logger.exception(f"PDF generation failed: {str(e)}")
        raise
