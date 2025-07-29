"""WeasyPrint implementation of the PageForge PDF rendering engine.

This module provides a concrete implementation of the Engine abstract class
that uses WeasyPrint to generate PDFs from DocumentData objects. WeasyPrint is
a visual rendering engine for HTML and CSS that can export to PDF.

Key Features:
- HTML/CSS-based rendering pipeline
- W3C standards compliance
- Advanced typography with proper kerning and ligatures
- Support for web fonts and CSS styling
- Alternative to the ReportLab engine

This engine is currently in development and provides basic functionality.

Note: WeasyPrint requires Cairo, Pango and GDK-PixBuf to be installed.
"""

import time
import uuid
import warnings
import importlib.util
from typing import Optional, Union

from ..core.models import DocumentData, ImageData, Section
from ..utils.config import get_config
from .engine_base import Engine

# Flag to check if WeasyPrint and its system dependencies are available
WEASYPRINT_AVAILABLE = False

# Check if weasyprint module exists first
if importlib.util.find_spec("weasyprint") is not None:
    try:
        # Try importing the module - this will fail if system libs are missing
        from weasyprint import CSS, HTML
        from weasyprint.text.fonts import FontConfiguration
        WEASYPRINT_AVAILABLE = True
    except (ImportError, OSError) as e:
        warnings.warn(f"WeasyPrint is installed but system dependencies are missing: {e}")
        # Create dummy objects to avoid import errors when the module is imported
        # but not actually used
        class CSS:
            pass
        class HTML:
            pass
        class FontConfiguration:
            pass


class WeasyPrintEngine(Engine):
    """WeasyPrint implementation of the PDF rendering engine.
    
    This engine uses the WeasyPrint library to generate PDFs from DocumentData.
    WeasyPrint converts HTML/CSS content to PDF, providing an alternative
    rendering approach to the ReportLab engine.
    
    Attributes:
        PAGE_WIDTH (float): Width of the page in points
        PAGE_HEIGHT (float): Height of the page in points
        MARGIN (float): Margin size in points
        MAX_IMAGES (int): Maximum number of images allowed per document
        DEFAULT_FONT (str): Default font name
        DEFAULT_FONT_SIZE (int): Default font size in points
    """
    
    def __init__(self, name: Optional[str] = "WeasyPrint"):
        """Initialize the WeasyPrint engine with configuration and logging.
        
        Args:
            name: Optional name for this engine instance
        """
        super().__init__(name=name)
        
        if not WEASYPRINT_AVAILABLE:
            self.logger.error("WeasyPrint library is not available. PDF generation will fail.")
        
        # Load configuration
        config = get_config()
        
        # Set rendering parameters from config
        self.PAGE_WIDTH: float = config.page.width
        self.PAGE_HEIGHT: float = config.page.height
        self.MARGIN: float = config.page.margin
        self.MAX_IMAGES: int = config.image.max_count
        
        # Default font settings
        self.DEFAULT_FONT: str = config.text.default_font
        self.DEFAULT_FONT_SIZE: int = config.text.default_size
        
        # Generate a unique ID for this rendering instance
        self.render_id: str = str(uuid.uuid4())[:8]
        
        self.logger.debug(
            f"WeasyPrintEngine initialized with config: page={self.PAGE_WIDTH}x{self.PAGE_HEIGHT}, "
            f"margin={self.MARGIN}, max_images={self.MAX_IMAGES}"
        )
    
    def _render(self, doc: DocumentData) -> bytes:
        """Internal render method that creates the PDF document using WeasyPrint.
        
        This method converts the DocumentData into HTML/CSS and then uses
        WeasyPrint to render the final PDF.
        
        Args:
            doc: The DocumentData object to render
            
        Returns:
            PDF contents as bytes
            
        Raises:
            ValueError: If document structure is invalid or rendering fails
            ImportError: If WeasyPrint is not installed
            TypeError: If expected types are incorrect
        """
        if not WEASYPRINT_AVAILABLE:
            self.logger.error("Cannot render PDF: WeasyPrint library is not available")
            raise ImportError("WeasyPrint library is not available. Install it with 'pip install weasyprint'")
        
        start_time = time.time()
        self.logger.info(f"Starting WeasyPrint PDF rendering (ID: {self.render_id})")
        
        try:
            # Build HTML content from document data
            html_content = self._build_html_content(doc)
            
            # Configure fonts
            font_config = FontConfiguration()
            
            # Create HTML object from string content
            html = HTML(string=html_content)
            
            # Generate PDF
            pdf_bytes = html.write_pdf(font_config=font_config)
            
            # Log completion with timing information
            elapsed = time.time() - start_time
            pdf_size = len(pdf_bytes)
            self.logger.info(
                f"PDF rendering complete (ID: {self.render_id}) - "
                f"time: {round(elapsed, 3)}s, size: {pdf_size} bytes"
            )
            return pdf_bytes
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"Failed to generate PDF after {elapsed:.2f} seconds: {str(e)}")
            raise ValueError(f"PDF generation failed: {str(e)}")
    
    def _build_html_content(self, doc: DocumentData) -> str:
        """Build HTML content from DocumentData.
        
        This method converts the DocumentData sections into HTML markup that
        WeasyPrint can render to PDF.
        
        Args:
            doc: The DocumentData object to convert to HTML
            
        Returns:
            Complete HTML document as a string
        """
        html_parts = []
        
        # Start HTML document
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html>')
        html_parts.append('<head>')
        html_parts.append(f'<title>{doc.title}</title>')
        html_parts.append('<style>')
        html_parts.append(self._get_default_css())
        html_parts.append('</style>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        
        # Add document title
        html_parts.append(f'<h1>{doc.title}</h1>')
        
        # Process sections
        for section in doc.sections:
            html_parts.append(self._process_section(section))
        
        # Process images (if any)
        if hasattr(doc, "images") and doc.images:
            html_parts.append('<div class="images">')
            for _i, image in enumerate(doc.images[:self.MAX_IMAGES]):
                try:
                    img_data_uri = self._image_to_data_uri(image)
                    html_parts.append('<div class="image-container">')
                    html_parts.append(f'<img src="{img_data_uri}" alt="{image.name}" />')
                    html_parts.append('</div>')
                except Exception as e:
                    self.logger.warning(f"Failed to process image '{image.name}': {e}")
            html_parts.append('</div>')
        
        # Close HTML document
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)
    
    def _process_section(self, section: Section) -> str:
        """Convert a document section to HTML markup.
        
        Args:
            section: The Section object to convert
            
        Returns:
            HTML markup for the section
        """
        stype = section.type
        
        if stype == "header":
            return f'<header>{section.text}</header>'
        
        elif stype == "footer":
            return f'<footer>{section.text}</footer>'
        
        elif stype == "paragraph":
            return f'<p>{section.text}</p>'
        
        elif stype == "table" and section.rows:
            table_html = ['<table>']
            for row in section.rows:
                cells = ['<td>' + str(cell) + '</td>' for cell in row]
                table_html.append('<tr>' + ''.join(cells) + '</tr>')
            table_html.append('</table>')
            return '\n'.join(table_html)
        
        elif stype == "list" and section.items:
            list_html = ['<ul>']
            for item in section.items:
                list_html.append(f'<li>{item}</li>')
            list_html.append('</ul>')
            return '\n'.join(list_html)
        
        else:
            self.logger.warning(f"Unknown or empty section type: {stype}")
            return ""
    
    def _image_to_data_uri(self, image: ImageData) -> str:
        """Convert image data to a data URI for embedding in HTML.
        
        Args:
            image: The ImageData object to convert
            
        Returns:
            Data URI string representation of the image
        """
        import base64
        fmt = image.format.lower()
        mime_type = f"image/{fmt}" if fmt != "jpg" else "image/jpeg"
        encoded = base64.b64encode(image.data).decode('ascii')
        return f"data:{mime_type};base64,{encoded}"
    
    def _get_default_css(self) -> str:
        """Generate default CSS styles for the PDF.
        
        Returns:
            CSS rules as a string
        """
        return """
        body {
            font-family: Arial, sans-serif;
            margin: 1cm;
            line-height: 1.5;
        }
        h1 {
            font-size: 18pt;
            margin-bottom: 12pt;
        }
        p {
            margin-bottom: 8pt;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 12pt;
        }
        td, th {
            border: 1px solid #ddd;
            padding: 6pt;
        }
        ul {
            margin-bottom: 12pt;
        }
        header {
            position: running(header);
            font-size: 10pt;
        }
        footer {
            position: running(footer);
            font-size: 10pt;
        }
        @page {
            @top-center { content: element(header); }
            @bottom-center { content: element(footer); }
            size: letter portrait;
            margin: 2cm;
        }
        .images {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-around;
            margin: 20pt 0;
        }
        .image-container {
            margin: 10pt;
            text-align: center;
        }
        img {
            max-width: 80%;
            max-height: 300pt;
        }
        """

