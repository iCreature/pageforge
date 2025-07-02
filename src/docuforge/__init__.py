from .models import DocumentData
from .builder import DocumentBuilder
from .engines.reportlab_engine import ReportLabEngine

def generate_pdf(data, engine="reportlab"):
    """
    Public API: Generate PDF bytes from structured data (dict or DocumentData).
    """
    if isinstance(data, dict):
        # Filter out unknown keys for DocumentData
        doc_fields = {k: v for k, v in data.items() if k in DocumentData.__dataclass_fields__}
        doc = DocumentData(**doc_fields)
    elif isinstance(data, DocumentData):
        doc = data
    else:
        raise TypeError("Input must be dict or DocumentData")
    # For now, only support ReportLab
    engine = ReportLabEngine()
    return engine.render(doc)
