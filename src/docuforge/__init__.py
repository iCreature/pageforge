import os

# First, import all modules to avoid circular imports
from .models import DocumentData
from .builder import DocumentBuilder
from .engines.reportlab_engine import ReportLabEngine

# After all modules are imported, set up logging
from .logging_config import get_logger, init_logging, TRACE_ID

# Initialize logging
log_file = os.environ.get('DOCUFORGE_LOG_FILE', None)
init_logging(log_file=log_file)

# Create package-level logger
logger = get_logger(__name__, {'trace_id': TRACE_ID})
logger.info(f"DocuForge initialized with trace ID: {TRACE_ID}")

def generate_pdf(data, engine="reportlab"):
    """
    Public API: Generate PDF bytes from structured data (dict or DocumentData).
    
    Args:
        data: Input data as dict or DocumentData object
        engine: Name of the rendering engine to use (default: "reportlab")
        
    Returns:
        PDF document as bytes
        
    Raises:
        TypeError: If data is not a dict or DocumentData object
        ValueError: If the engine is not supported or document structure is invalid
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
            raise TypeError("Input must be dict or DocumentData")
            
        # For now, only support ReportLab
        engine_obj = ReportLabEngine()
        logger.info(f"Rendering document with {len(getattr(doc, 'sections', []))} sections and {len(getattr(doc, 'images', []))} images")
        result = engine_obj.render(doc)
        logger.info(f"PDF generation complete, size: {len(result)} bytes")
        return result
    except Exception as e:
        logger.exception(f"PDF generation failed: {str(e)}")
        raise
