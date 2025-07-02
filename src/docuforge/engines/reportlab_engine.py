from .engine_base import Engine
from ..models import DocumentData

class ReportLabEngine(Engine):
    def _render(self, doc: DocumentData) -> bytes:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        import io

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        y = 750
        # Draw title
        text = getattr(doc, "title", None) or "DocuForge PDF"
        c.drawString(100, y, text)
        y -= 30

        # Draw sections
        if hasattr(doc, "sections"):
            for section in doc.sections:
                if isinstance(section, dict):
                    section_type = section.get("type")
                else:
                    section_type = getattr(section, "type", None)
                if section_type == "paragraph":
                    stext = section["text"] if isinstance(section, dict) else getattr(section, "text", "")
                    c.drawString(100, y, stext)
                    y -= 20
                elif section_type == "table":
                    rows = section["rows"] if isinstance(section, dict) else getattr(section, "rows", [])
                    if rows:
                        # Draw headers
                        c.drawString(100, y, " | ".join(str(cell) for cell in rows[0]))
                        y -= 20
                        # Draw first row after header (if present)
                        if len(rows) > 1:
                            c.drawString(100, y, " | ".join(str(cell) for cell in rows[1]))
                            y -= 20
        # Draw first image if present
        if hasattr(doc, "images") and doc.images:
            img = doc.images[0]
            img_data = img["data"] if isinstance(img, dict) else getattr(img, "data", None)
            if img_data:
                try:
                    img_stream = io.BytesIO(img_data)
                    # Use drawImage for better XObject detection
                    c.drawImage(ImageReader(img_stream), 100, y-120, width=120, height=120)
                    y -= 140
                except Exception:
                    pass  # Don't fail if image is invalid
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()
