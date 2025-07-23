import pytest
from docuforge import generate_pdf
from docuforge.core.models import DocumentData, Section
from pypdf import PdfReader
import io

def test_custom_font_size(monkeypatch):
    # Monkeypatch engine to use a large font
    from docuforge.engines import reportlab_engine
    orig_render = reportlab_engine.ReportLabEngine._render
    def big_font_render(self, doc):
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        import io
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica", 36)
        c.drawString(100, 700, doc.title)
        c.save()
        buffer.seek(0)
        return buffer.read()
    monkeypatch.setattr(reportlab_engine.ReportLabEngine, "_render", big_font_render)
    doc = DocumentData(title="Big Font", sections=[], images=[])
    pdf_bytes = generate_pdf(doc)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "Big Font" in text
    # Restore
    monkeypatch.setattr(reportlab_engine.ReportLabEngine, "_render", orig_render)
