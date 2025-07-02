try:
    from .engine_base import Engine
    from ..models import DocumentData
    from ..logging_config import get_logger
except ImportError:
    # For testing when imported directly
    from docuforge.engines.engine_base import Engine
    from docuforge.models import DocumentData
    from docuforge.logging_config import get_logger

import io
import time
import uuid
from typing import Optional, Dict, List, Any, Tuple, Union
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


class ReportLabEngine(Engine):
    """
    ReportLab implementation of the PDF rendering engine.
    
    This engine uses the ReportLab library to generate PDFs from DocumentData objects.
    It supports Unicode text, tables, lists, and image embedding with various
    validation and error handling features.
    
    Attributes:
        PAGE_WIDTH: Width of the page in points
        PAGE_HEIGHT: Height of the page in points
        MARGIN: Margin size in points
        LINE_HEIGHT: Height of a line of text in points
        IMAGE_HEIGHT: Default height for embedded images
        IMAGE_WIDTH: Default width for embedded images
        MAX_IMAGES: Maximum number of images allowed in a document
    """
    # Define class-wide default constants
    PAGE_WIDTH, PAGE_HEIGHT = letter
    MARGIN = 50
    LINE_HEIGHT = 18
    IMAGE_HEIGHT = 120
    IMAGE_WIDTH = 120
    MAX_IMAGES = 10
    
    def __init__(self, name: Optional[str] = "ReportLab"):
        """
        Initialize the ReportLab engine with configuration and logging.
        
        Args:
            name: Optional name for this engine instance
        """
        super().__init__(name=name)
        
        # Copy class constants to instance attributes for easy access
        self.PAGE_WIDTH, self.PAGE_HEIGHT = self.__class__.PAGE_WIDTH, self.__class__.PAGE_HEIGHT
        self.MARGIN = self.__class__.MARGIN
        self.LINE_HEIGHT = self.__class__.LINE_HEIGHT
        self.IMAGE_HEIGHT = self.__class__.IMAGE_HEIGHT
        self.IMAGE_WIDTH = self.__class__.IMAGE_WIDTH
        self.MAX_IMAGES = self.__class__.MAX_IMAGES
        
        # Generate a unique ID for this rendering instance
        self.render_id = str(uuid.uuid4())[:8]
    
    def _render(self, doc: DocumentData) -> bytes:
        """
        Internal render method that creates the PDF document using ReportLab.
        
        Args:
            doc: The DocumentData object to render
            
        Returns:
            PDF contents as bytes
            
        Raises:
            ValueError: If document structure is invalid or rendering fails
            TypeError: If expected types are incorrect
        """
        start_time = time.time()
        
        # Create a render context for logging
        context = {
            'render_id': self.render_id,
            'doc_title': getattr(doc, 'title', 'Untitled'),
            'sections_count': len(getattr(doc, 'sections', [])),
            'images_count': len(getattr(doc, 'images', []))
        }
        
        # Get logger with context
        logger = self.logger.adapter.extra['context'] if hasattr(self.logger, 'adapter') else {}
        logger.update(context)
        
        self.logger.info(f"Starting PDF rendering with ReportLab (ID: {self.render_id})")
        # Create PDF canvas
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        self.logger.debug("Created ReportLab canvas with letter size page")
        
        # Register built-in Unicode fonts
        font_name = "Helvetica"  # Default font
        registered_fonts = []
        
        try:
            # Register CID fonts for various scripts
            cid_fonts = [
                ('HeiseiMin-W3', 'Japanese'),
                ('HYSMyeongJo-Medium', 'Korean'),
                ('STSong-Light', 'Simplified Chinese')
            ]
            
            for font_id, language in cid_fonts:
                try:
                    pdfmetrics.registerFont(UnicodeCIDFont(font_id))
                    registered_fonts.append(font_id)
                    self.logger.debug(f"Registered {language} font: {font_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to register {language} font {font_id}: {str(e)}")
            
            if registered_fonts:
                self.logger.info(f"Registered {len(registered_fonts)} Unicode CID fonts for international text support")
            else:
                self.logger.warning("No Unicode fonts were registered, falling back to Helvetica only")
        except Exception as e:
            self.logger.error(f"Font registration error: {str(e)}, using Helvetica only")
            
        # Set initial font
        c.setFont(font_name, 14)
        self.logger.info(f"Rendering PDF for document: '{getattr(doc, 'title', 'Untitled')}'")

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
                    self.logger.warning(f"Error extracting header/footer: {e}")

        # Helper to draw header and footer
        def draw_header_footer(page_num):
            if header:
                c.setFont(font_name, 12)
                c.drawString(self.MARGIN, self.PAGE_HEIGHT - self.MARGIN + 10, header)
            if footer:
                c.setFont(font_name, 10)
                c.drawString(self.MARGIN, self.MARGIN - 20, f"{footer} | Page {page_num}")
            c.setFont(font_name, 14)

        # Helper to check for page break
        def ensure_space(h):
            nonlocal y, page_num
            if y - h < self.MARGIN:
                c.showPage()
                page_num += 1
                y = self.PAGE_HEIGHT - self.MARGIN
                draw_header_footer(page_num)
                c.setFont(font_name, 14)
        
        # Initial setup
        y = self.PAGE_HEIGHT - self.MARGIN
        page_num = 1
        draw_header_footer(page_num)

        # Title
        title = "DocuForge PDF"
        if hasattr(doc, "title") and doc.title:
            title = doc.title
            
        c.setFont(font_name, 16)
        c.drawString(self.MARGIN, y, text=title)
        y -= self.LINE_HEIGHT * 2
        c.setFont(font_name, 14)

        # Process sections
        if hasattr(doc, "sections") and doc.sections:
            for section in doc.sections:
                try:
                    # Extract section type safely
                    stype = None
                    if isinstance(section, dict):
                        if "type" not in section:
                            self.logger.warning(f"Section missing type: {section}")
                            raise ValueError(f"Section missing type field: {section}")
                        stype = section["type"]
                    elif hasattr(section, "type"):
                        stype = section.type
                    else:
                        self.logger.warning(f"Cannot determine section type: {section}")
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
                            
                        ensure_space(self.LINE_HEIGHT)
                        self._set_appropriate_font(c, stext, font_name, 14)
                        c.drawString(self.MARGIN, y, text=stext)
                        y -= self.LINE_HEIGHT
                        
                    elif stype == "table":
                        # Extract rows safely
                        rows = []
                        if isinstance(section, dict):
                            rows = section.get("rows", [])
                        else:
                            rows = getattr(section, "rows", [])
                            
                        # Validate rows is iterable
                        if not hasattr(rows, "__iter__"):
                            self.logger.warning(f"Table rows must be iterable, got: {type(rows).__name__}")
                            continue
                            
                        for row in rows:
                            try:
                                # Convert row to string cells
                                if not isinstance(row, (list, tuple)):
                                    # Convert non-list row to a single cell
                                    row_cells = [str(row)]
                                    self.logger.warning(f"Converting non-list row to single cell: {row}")
                                else:
                                    row_cells = [str(cell) for cell in row]
                                    
                                # Draw the row
                                ensure_space(self.LINE_HEIGHT)
                                row_text = " | ".join(row_cells)
                                self._set_appropriate_font(c, row_text, font_name, 14)
                                c.drawString(self.MARGIN, y, text=row_text)
                                y -= self.LINE_HEIGHT
                            except Exception as e:
                                self.logger.warning(f"Error processing table row: {e}")
                                
                    elif stype == "list":
                        # Get list items safely
                        items = []
                        if isinstance(section, dict):
                            items = section.get("items", [])
                        else:
                            items = getattr(section, "items", [])
                            
                        for item in items:
                            try:
                                ensure_space(self.LINE_HEIGHT)
                                item_text = f"• {item}"
                                self._set_appropriate_font(c, item_text, font_name, 14)
                                c.drawString(self.MARGIN + 20, y, text=item_text)
                                y -= self.LINE_HEIGHT
                            except Exception as e:
                                self.logger.warning(f"Error processing list item: {e}")
                    else:
                        self.logger.warning(f"Unknown section type: {stype}")
                        raise ValueError(f"Unknown section type: {stype}")
                except Exception as e:
                    self.logger.warning(f"Error processing section: {e}")
                    raise ValueError(f"Failed to render section: {e}")
                    
        # Process images
        if hasattr(doc, "images") and doc.images:
            images = doc.images
            # Limit to 10 images max
            if len(images) > self.MAX_IMAGES:
                self.logger.warning(f"Too many images supplied ({len(images)}); only the first {self.MAX_IMAGES} will be embedded.")
                images = images[:self.MAX_IMAGES]
                
            for img in images:
                try:
                    # Extract image data safely
                    img_data = None
                    if isinstance(img, dict):
                        img_data = img.get("data")
                    else:
                        img_data = getattr(img, "data", None)
                        
                    if img_data:
                        ensure_space(self.IMAGE_HEIGHT)
                        img_stream = io.BytesIO(img_data)
                        c.drawImage(
                            ImageReader(img_stream),
                            self.MARGIN,
                            y - self.IMAGE_HEIGHT,
                            width=self.IMAGE_WIDTH,
                            height=self.IMAGE_HEIGHT
                        )
                        y -= self.IMAGE_HEIGHT + 10
                    else:
                        img_name = img.get("name", "unknown") if isinstance(img, dict) else getattr(img, "name", "unknown")
                        self.logger.warning(f"Image {img_name} has no data")
                        raise ValueError(f"Image {img_name} has no data")
                except Exception as e:
                    self.logger.warning(f"Error embedding image: {e}")
                    raise ValueError(f"Failed to render image: {e}")
                    
        # Finalize PDF
        try:
            c.showPage()
            c.save()
            buffer.seek(0)
            pdf_data = buffer.read()
            
            # Log completion with timing information
            elapsed = time.time() - start_time
            pdf_size = len(pdf_data)
            self.logger.info(
                f"PDF rendering complete (ID: {self.render_id}) - "
                f"time: {round(elapsed, 3)}s, size: {pdf_size} bytes, pages: {page_num}"
            )
            return pdf_data
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"Failed to finalize PDF after {elapsed:.2f} seconds: {str(e)}")
            raise ValueError(f"PDF finalization failed: {str(e)}")

    def _set_appropriate_font(self, canvas, text: str, default_font: str, size: int) -> str:
        """
        Set the appropriate font based on text content.
        
        Analyzes the text content and selects the most appropriate font
        for rendering based on the Unicode character ranges present.
        
        Args:
            canvas: ReportLab canvas object
            text: Text to analyze for font selection
            default_font: Default font name to use if no specific font is needed
            size: Font size to set
            
        Returns:
            Name of the font that was selected and set
        """
        # Define Unicode character ranges for different scripts
        ranges = {
            'japanese': [(0x3040, 0x309F), (0x30A0, 0x30FF)],
            'korean': [(0xAC00, 0xD7AF)],
            'chinese': [(0x4E00, 0x9FFF), (0x3000, 0x303F)],
            'arabic': [(0x0600, 0x06FF)],
            'cyrillic': [(0x0400, 0x04FF)],
            'hebrew': [(0x0590, 0x05FF)]
        }
        
        # Font mapping for scripts
        font_map = {
            'japanese': 'HeiseiMin-W3',
            'korean': 'HYSMyeongJo-Medium',
            'chinese': 'STSong-Light',
            'arabic': 'STSong-Light',  # Fallback, not ideal for Arabic
            'hebrew': 'STSong-Light',  # Fallback, not ideal for Hebrew
            'cyrillic': default_font,  # Default font usually works for Cyrillic
            'default': default_font
        }
        
        try:
            # Detect script based on character ranges
            detected_script = 'default'
            for script, char_ranges in ranges.items():
                if any(any(start <= ord(c) <= end for start, end in char_ranges) for c in text):
                    detected_script = script
                    break
            
            # Select and set font based on detected script
            selected_font = font_map.get(detected_script, default_font)
            
            try:
                canvas.setFont(selected_font, size)
                if detected_script != 'default':
                    self.logger.debug(f"Selected {detected_script} font '{selected_font}' for text")
                return selected_font
            except Exception as e:
                self.logger.warning(f"Failed to set {detected_script} font '{selected_font}': {str(e)}")
                canvas.setFont(default_font, size)
                return default_font
                
        except Exception as e:
            # If any error occurs during font detection, fall back to default
            self.logger.warning(f"Font detection error: {str(e)}, falling back to {default_font}")
            canvas.setFont(default_font, size)
            return default_font
