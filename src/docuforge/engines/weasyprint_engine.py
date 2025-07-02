from .engine_base import Engine
from ..models import DocumentData

class WeasyPrintEngine(Engine):
    def _render(self, doc: DocumentData) -> bytes:
        # For now, just mock output for tests
        return b"PDFDATA2"
