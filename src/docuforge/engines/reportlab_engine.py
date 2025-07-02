try:
    from .engine_base import Engine
    from ..models import DocumentData
except ImportError:
    # For testing when imported directly
    from docuforge.engines.engine_base import Engine
    from docuforge.models import DocumentData

import io
import logging
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

logger = logging.getLogger("docuforge.reportlab")


class ReportLabEngine(Engine):
    def _render(self, doc: DocumentData) -> bytes:
        """Internal render method that creates the PDF document.
        
        Args:
            doc: The DocumentData object to render
            
        Returns:
            PDF contents as bytes
        """
        PAGE_WIDTH, PAGE_HEIGHT = letter
        MARGIN = 50
        LINE_HEIGHT = 18
        IMAGE_HEIGHT = 120
        IMAGE_WIDTH = 120
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Register built-in Unicode fonts
        try:
            # Register CID fonts for various scripts
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))        # Japanese
            pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))  # Korean
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))        # Simplified Chinese
            
            # Use Helvetica for Latin and CID fonts for non-Latin as needed
            font_name = "Helvetica"  # Default font
            logger.info("Using ReportLab built-in Unicode fonts for non-Latin scripts")
        except Exception as e:
            font_name = "Helvetica"
            logger.warning(f"Failed to register Unicode fonts: {e}, falling back to Helvetica only.")
            
        c.setFont(font_name, 14)
        logger.info(f"Rendering PDF for doc title: {getattr(doc, 'title', None)}")

        # Process header and footer from document or sections
        header = getattr(doc, "header", None)
        footer = getattr(doc, "footer", None)
        
        # Check for header/footer in sections
        if hasattr(doc, "sections") and doc.sections:
            for section in doc.sections:
                try:
                    if isinstance(section, dict) and "type" in section:
                        stype = section["type"]
                        if stype == "header" and not header:
                            header = section.get("text", "")
                        elif stype == "footer" and not footer:
                            footer = section.get("text", "")
                    elif hasattr(section, "type"):
                        stype = section.type
                        if stype == "header" and not header:
                            header = getattr(section, "text", "")
                        elif stype == "footer" and not footer:
                            footer = getattr(section, "text", "")
                except (TypeError, AttributeError, KeyError) as e:
                    logger.warning(f"Error extracting header/footer: {e}")

        # Helper to draw header and footer
        def draw_header_footer(page_num):
            if header:
                c.setFont(font_name, 12)
                c.drawString(MARGIN, PAGE_HEIGHT - MARGIN + 10, header)
            if footer:
                c.setFont(font_name, 10)
                c.drawString(MARGIN, MARGIN - 20, f"{footer} | Page {page_num}")
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
        
        # Initial setup
        y = PAGE_HEIGHT - MARGIN
        page_num = 1
        draw_header_footer(page_num)

        # Title
        title = "DocuForge PDF"
        if hasattr(doc, "title") and doc.title:
            title = doc.title
            
        c.setFont(font_name, 16)
        c.drawString(MARGIN, y, text=title)
        y -= LINE_HEIGHT * 2
        c.setFont(font_name, 14)

        # Process sections
        if hasattr(doc, "sections") and doc.sections:
            for section in doc.sections:
                try:
                    # Extract section type safely
                    stype = None
                    if isinstance(section, dict):
                        if "type" not in section:
                            logger.warning(f"Section missing type: {section}")
                            raise ValueError(f"Section missing type field: {section}")
                        stype = section["type"]
                    elif hasattr(section, "type"):
                        stype = section.type
                    else:
                        logger.warning(f"Cannot determine section type: {section}")
                        raise ValueError(f"Cannot determine section type: {section}")
                        
                    # Skip header and footer sections as they're already handled
                    if stype in ["header", "footer"]:
                        continue

                    # Process section based on its type
                    if stype == "paragraph":
                        # Get text content safely
                        stext = ""
                        if isinstance(section, dict):
                            stext = section.get("text", "")
                        else:
                            stext = getattr(section, "text", "")
                            
                        ensure_space(LINE_HEIGHT)
                        self._set_appropriate_font(c, stext, font_name, 14)
                        c.drawString(MARGIN, y, text=stext)
                        y -= LINE_HEIGHT
                        
                    elif stype == "table":
                        # Extract rows safely
                        rows = []
                        if isinstance(section, dict):
                            rows = section.get("rows", [])
                        else:
                            rows = getattr(section, "rows", [])
                            
                        # Validate rows is iterable
                        if not hasattr(rows, "__iter__"):
                            logger.warning(f"Table rows must be iterable, got: {type(rows).__name__}")
                            continue
                            
                        for row in rows:
                            try:
                                # Convert row to string cells
                                if not isinstance(row, (list, tuple)):
                                    # Convert non-list row to a single cell
                                    row_cells = [str(row)]
                                    logger.warning(f"Converting non-list row to single cell: {row}")
                                else:
                                    row_cells = [str(cell) for cell in row]
                                    
                                # Draw the row
                                ensure_space(LINE_HEIGHT)
                                row_text = " | ".join(row_cells)
                                self._set_appropriate_font(c, row_text, font_name, 14)
                                c.drawString(MARGIN, y, text=row_text)
                                y -= LINE_HEIGHT
                            except Exception as e:
                                logger.warning(f"Error processing table row: {e}")
                                
                    elif stype == "list":
                        # Get list items safely
                        items = []
                        if isinstance(section, dict):
                            items = section.get("items", [])
                        else:
                            items = getattr(section, "items", [])
                            
                        for item in items:
                            try:
                                ensure_space(LINE_HEIGHT)
                                item_text = f"• {item}"
                                self._set_appropriate_font(c, item_text, font_name, 14)
                                c.drawString(MARGIN + 20, y, text=item_text)
                                y -= LINE_HEIGHT
                            except Exception as e:
                                logger.warning(f"Error processing list item: {e}")
                    else:
                        logger.warning(f"Unknown section type: {stype}")
                        raise ValueError(f"Unknown section type: {stype}")
                except Exception as e:
                    logger.warning(f"Error processing section: {e}")
                    raise ValueError(f"Failed to render section: {e}")
                    
        # Process images
        if hasattr(doc, "images") and doc.images:
            images = doc.images
            # Limit to 10 images max
            if len(images) > 10:
                logger.warning(f"Too many images supplied ({len(images)}); only the first 10 will be embedded.")
                images = images[:10]
                
            for img in images:
                try:
                    # Extract image data safely
                    img_data = None
                    if isinstance(img, dict):
                        img_data = img.get("data")
                    else:
                        img_data = getattr(img, "data", None)
                        
                    if img_data:
                        ensure_space(IMAGE_HEIGHT)
                        img_stream = io.BytesIO(img_data)
                        c.drawImage(
                            ImageReader(img_stream),
                            MARGIN,
                            y - IMAGE_HEIGHT,
                            width=IMAGE_WIDTH,
                            height=IMAGE_HEIGHT
                        )
                        y -= IMAGE_HEIGHT + 10
                    else:
                        img_name = img.get("name", "unknown") if isinstance(img, dict) else getattr(img, "name", "unknown")
                        logger.warning(f"Image {img_name} has no data")
                        raise ValueError(f"Image {img_name} has no data")
                except Exception as e:
                    logger.warning(f"Error embedding image: {e}")
                    raise ValueError(f"Failed to render image: {e}")
                    
        # Finalize PDF
        try:
            c.showPage()
            c.save()
            buffer.seek(0)
            pdf_data = buffer.read()
            logger.info(f"PDF rendering complete, size: {len(pdf_data)} bytes")
            return pdf_data
        except Exception as e:
            logger.error(f"Failed to finalize PDF: {e}")
            raise

    def _set_appropriate_font(self, canvas, text, default_font, size):
        """Set the appropriate font based on text content.
        
        Args:
            canvas: ReportLab canvas object
            text: Text to analyze for font selection
            default_font: Default font name to use
            size: Font size to set
        """
        try:
            # Check for CJK (Chinese, Japanese, Korean) characters
            has_cjk = any(0x3000 <= ord(c) <= 0x9FFF or 0xF900 <= ord(c) <= 0xFAFF or 0xFF00 <= ord(c) <= 0xFFEF for c in text)
            has_arabic = any(0x0600 <= ord(c) <= 0x06FF for c in text)
            has_cyrillic = any(0x0400 <= ord(c) <= 0x04FF for c in text)
            
            if has_cjk:
                # Use appropriate CID font for CJK text
                try:
                    if any(0x3040 <= ord(c) <= 0x309F or 0x30A0 <= ord(c) <= 0x30FF for c in text):
                        # Japanese specific
                        canvas.setFont('HeiseiMin-W3', size)
                    elif any(0xAC00 <= ord(c) <= 0xD7AF for c in text):
                        # Korean specific
                        canvas.setFont('HYSMyeongJo-Medium', size)
                    else:
                        # Default Chinese
                        canvas.setFont('STSong-Light', size)
                    return
                except Exception:
                    pass  # Fall back to default if specific font fails
                    
            elif has_arabic:
                # Arabic text would render better with a specific font
                # but we'll use default since most RTL rendering issues
                # are about layout, not the font itself
                pass
                    
            elif has_cyrillic:
                # Cyrillic works with default font
                pass
                
            # Default font for all other scripts or if specific font failed
            canvas.setFont(default_font, size)
        except Exception as e:
            # If any error occurs during font detection, fall back to default
            logger.warning(f"Font detection error: {e}, falling back to {default_font}")
            canvas.setFont(default_font, size)
