from .engine_base import Engine
from ..models import DocumentData

import logging
logger = logging.getLogger("docuforge.reportlab")

class ReportLabEngine(Engine):
    def _render(self, doc: DocumentData) -> bytes:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from reportlab.lib import fonts
        import io

        PAGE_WIDTH, PAGE_HEIGHT = letter
        MARGIN = 50
        LINE_HEIGHT = 18
        IMAGE_HEIGHT = 120
        IMAGE_WIDTH = 120
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        font_name = "Helvetica"
        c.setFont(font_name, 14)

        logger.info(f"Rendering PDF for doc title: {getattr(doc, 'title', None)}")

        def draw_header_footer(page_num):
            header = getattr(doc, "header", None) or next((s["text"] for s in getattr(doc, "sections", []) if s.get("type") == "header"), None)
            footer = getattr(doc, "footer", None) or next((s["text"] for s in getattr(doc, "sections", []) if s.get("type") == "footer"), None)
            if header:
                c.setFont(font_name, 12)
                c.drawString(MARGIN, PAGE_HEIGHT - MARGIN + 10, header)
            if footer:
                c.setFont(font_name, 10)
                c.drawString(MARGIN, MARGIN - 20, f"{footer} | Page {page_num}")
            c.setFont(font_name, 14)

        y = PAGE_HEIGHT - MARGIN
        page_num = 1
        draw_header_footer(page_num)
        # Title
        text = getattr(doc, "title", None) or "DocuForge PDF"
        c.setFont(font_name, 16)
        c.drawString(MARGIN, y, text)
        y -= LINE_HEIGHT * 2
        c.setFont(font_name, 14)

        # Helper to check for page break
        def ensure_space(h):
            nonlocal y, page_num
            if y - h < MARGIN:
                c.showPage()
                page_num += 1
                y = PAGE_HEIGHT - MARGIN
                draw_header_footer(page_num)
                c.setFont(font_name, 14)

        # Draw sections
        if hasattr(doc, "sections"):
            for section in doc.sections:
                try:
                    if isinstance(section, dict):
                        section_type = section.get("type")
                    else:
                        section_type = getattr(section, "type", None)
                    if section_type == "header" or section_type == "footer":
                        continue  # Already handled
                    elif section_type == "paragraph":
                        stext = section["text"] if isinstance(section, dict) else getattr(section, "text", "")
                        ensure_space(LINE_HEIGHT)
                        c.drawString(MARGIN, y, stext)
                        y -= LINE_HEIGHT
                    elif section_type == "table":
                        rows = section["rows"] if isinstance(section, dict) else getattr(section, "rows", [])
                        for row in rows:
                            ensure_space(LINE_HEIGHT)
                            c.drawString(MARGIN, y, " | ".join(str(cell) for cell in row))
                            y -= LINE_HEIGHT
                    elif section_type == "list":
                        items = section["items"] if isinstance(section, dict) else getattr(section, "items", [])
                        for item in items:
                            ensure_space(LINE_HEIGHT)
                            c.drawString(MARGIN + 20, y, f"• {item}")
                            y -= LINE_HEIGHT
                    else:
                        logger.warning(f"Unknown section type: {section_type}")
                except Exception as e:
                    logger.error(f"Failed to render section {section}: {e}")
        # Draw all images
        if hasattr(doc, "images") and doc.images:
            for img in doc.images:
                img_data = img["data"] if isinstance(img, dict) else getattr(img, "data", None)
                if img_data:
                    ensure_space(IMAGE_HEIGHT)
                    try:
                        img_stream = io.BytesIO(img_data)
                        c.drawImage(ImageReader(img_stream), MARGIN, y - IMAGE_HEIGHT, width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
                        y -= IMAGE_HEIGHT + 10
                    except Exception as e:
                        logger.error(f"Failed to render image {getattr(img, 'name', None)}: {e}")
        try:
            c.showPage()
            c.save()
            buffer.seek(0)
            logger.info("PDF rendering complete.")
            return buffer.read()
        except Exception as e:
            logger.error(f"Failed to finalize PDF: {e}")
            raise
