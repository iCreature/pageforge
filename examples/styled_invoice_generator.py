#!/usr/bin/env python3
"""
Styled Invoice Generator
This script demonstrates alternative styling options for PDF invoices
"""
import os
import sys
import base64
from io import BytesIO
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import random

# Import directly from original invoice generator
from llm_invoice_generator import SimpleInvoiceLLM, process_prompt

# Import the pageforge package
import pageforge

# ReportLab imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Modern color scheme
COLORS = {
    'primary': colors.HexColor('#3498db'),      # Blue
    'secondary': colors.HexColor('#2ecc71'),    # Green  
    'accent': colors.HexColor('#e74c3c'),       # Red
    'dark': colors.HexColor('#2c3e50'),         # Dark blue/gray
    'light': colors.HexColor('#ecf0f1'),        # Light gray
    'text': colors.HexColor('#333333'),         # Dark gray for text
    'highlight': colors.HexColor('#f39c12')     # Orange highlight
}

@dataclass
class Section:
    """Document section"""
    type: str
    text: str = ""
    items: List[str] = None
    rows: List[List[str]] = None

@dataclass
class ImageData:
    """Image data"""
    name: str
    data: bytes
    format: str

@dataclass
class DocumentData:
    """Document data"""
    title: str
    sections: List[Section]
    images: List[ImageData] = None

class ModernPositionStrategy:
    """Modern logo positioning strategy that places logo at the top-center"""
    
    def position_logo(self, canvas, page_size, img, width, height):
        """Position the logo at the top center of the page"""
        # Calculate center position
        x = (page_size[0] - width) / 2
        y = page_size[1] - height - 36  # 36 points from top
        
        # Draw the logo
        img.drawOn(canvas, x, y)

class ModernNumberedCanvas(Canvas):
    """A canvas that adds page numbers and styling to each page"""
    def __init__(self, *args, **kwargs):
        Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.position_strategy = None
        self.logo_data = None
        self.footer_text = None
        self.background_color = COLORS['light']
        self.header_color = COLORS['primary']

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Add page numbers and design elements to each page"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_design(num_pages)
            Canvas.showPage(self)
        Canvas.save(self)

    def draw_page_design(self, page_count):
        """Draw the page design, including background, logo, and footer"""
        width, height = self._pagesize
        
        # Draw background elements
        self.setFillColor(self.background_color)
        self.rect(0, 0, width, height, stroke=0, fill=1)
        
        # Draw header bar
        self.setFillColor(self.header_color)
        self.rect(0, height - 1.5*inch, width, 1.5*inch, stroke=0, fill=1)
        
        # Draw footer bar
        self.setFillColor(COLORS['dark'])
        self.rect(0, 0, width, 0.75*inch, stroke=0, fill=1)
        
        # Add decorative elements
        self.setStrokeColor(COLORS['secondary'])
        self.setLineWidth(3)
        self.line(inch, height-1.5*inch-3, width-inch, height-1.5*inch-3)
        
        # Draw logo if available
        if self.logo_data and self.position_strategy:
            try:
                # Create image object from data
                img_data = BytesIO(self.logo_data.data)
                logo_width = 144  # 2 inches (72pts = 1 inch)
                logo_height = 72   # 1 inch
                
                # Create ReportLab image
                img = RLImage(img_data, width=logo_width, height=logo_height)
                
                # Position the logo using the strategy
                self.position_strategy.position_logo(
                    self, self._pagesize, img, logo_width, logo_height
                )
            except Exception as e:
                print(f"Error placing logo: {str(e)}")
        
        # Add footer with page numbers if footer text is available
        if self.footer_text:
            # Replace placeholders with actual values
            page_text = self.footer_text
            page_text = page_text.replace("{page_number}", str(self._pageNumber))
            page_text = page_text.replace("{total_pages}", str(page_count))
            
            # Draw the footer at the bottom of the page
            self.setFillColor(colors.white)
            self.setFont("Helvetica", 10)
            self.drawCentredString(width/2, 0.4*inch, page_text)

class ModernDocumentEngine:
    """Custom engine for modern styled PDF generation"""
    
    def __init__(self, position_strategy=None):
        """Initialize with a positioning strategy for logo placement"""
        self.position_strategy = position_strategy or ModernPositionStrategy()
        self.footer_text = None
        
    def create_document_with_logo(self, doc):
        """Create a modern styled PDF document with a logo
        
        Args:
            doc: The document data including content and optional logo
            
        Returns:
            bytes: The generated PDF
        """
        # Document creation
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1.75*inch,  # Extra top margin to avoid overlap with header
            bottomMargin=1*inch    # Extra bottom margin for footer
        )
        
        # Document content
        story = []
        
        # Create custom styles
        styles = self._create_styles()
        
        # Process sections (header, paragraphs, lists, tables, etc.)
        for section in doc.sections:
            self._process_section(story, section, styles)
        
        # Create a custom canvas maker
        def custom_canvas_maker(filename, pagesize=A4, **kwargs):
            # Create our numbered canvas
            canvas = ModernNumberedCanvas(filename, pagesize=pagesize, **kwargs)
            
            # Store reference to the logo strategy and data for use in draw_page_number
            canvas.position_strategy = self.position_strategy
            canvas.logo_data = doc.images[0] if doc.images and len(doc.images) > 0 else None
            canvas.footer_text = self.footer_text
            
            return canvas
        
        # Build the document with our custom canvas maker
        document.build(story, canvasmaker=custom_canvas_maker)
        
        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
        
    def _create_styles(self):
        """Create custom styles for the document"""
        styles = getSampleStyleSheet()
        
        # Override default styles
        styles['Normal'].fontName = "Helvetica"
        styles['Normal'].fontSize = 10
        styles['Normal'].textColor = COLORS['text']
        styles['Normal'].leading = 14
        
        # Create custom title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=24,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Create custom header style
        styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=COLORS['primary'],
            spaceAfter=12
        ))
        
        # Create custom subheader style
        styles.add(ParagraphStyle(
            name='CustomSubHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=COLORS['secondary'],
            spaceAfter=10
        ))
        
        # Create right-aligned text style
        styles.add(ParagraphStyle(
            name='RightAligned',
            parent=styles['Normal'],
            alignment=TA_RIGHT
        ))
        
        # Create centered text style
        styles.add(ParagraphStyle(
            name='CenteredText',
            parent=styles['Normal'],
            alignment=TA_CENTER
        ))
        
        # Create highlighted text style
        styles.add(ParagraphStyle(
            name='Highlighted',
            parent=styles['Normal'],
            textColor=COLORS['accent'],
            fontName='Helvetica-Bold'
        ))
        
        return styles
    
    def _process_section(self, story, section, styles):
        """Process a section and add it to the story"""
        # Skip sections with no text content if they're not special types
        if not getattr(section, 'text', None) and section.type not in ['table', 'list']:
            return
            
        # Add spacing before sections
        story.append(Spacer(1, 12))
        
        if section.type == "paragraph":
            story.append(Paragraph(section.text, styles['Normal']))
            
        elif section.type == "header":
            # The header is handled differently - first check if it's the document title
            if story:  # Not the first element
                story.append(Paragraph(section.text, styles['CustomHeader']))
            else:
                # This is the first element, likely the document title
                # We don't add it here as it's handled by the canvas
                self.document_title = section.text
            
        elif section.type == "list" and hasattr(section, 'items') and section.items:
            # Add each item as a paragraph with a bullet
            for item in section.items:
                bullet_text = f"• {item}"
                story.append(Paragraph(bullet_text, styles['Normal']))
                story.append(Spacer(1, 6))
            
        elif section.type == "table" and hasattr(section, 'rows') and section.rows:
            # Create a more modern table style
            data = section.rows
            table = Table(data, repeatRows=1)
            
            # Alternate row colors for better readability
            row_colors = [COLORS['light'], colors.white]
            
            table_style = TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                # Content styling
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                # Grid styling
                ('GRID', (0, 0), (-1, -1), 0.5, COLORS['dark']),
                ('LINEBELOW', (0, 0), (-1, 0), 2, COLORS['dark']),
                # Add subtle inner grid
                ('INNERGRID', (0, 0), (-1, -1), 0.25, COLORS['light']),
            ])
            
            # Add alternating row colors
            for i in range(1, len(data)):
                table_style.add('BACKGROUND', (0, i), (-1, i), row_colors[i % 2])
            
            # Price columns are right-aligned
            if len(data[0]) >= 3:  # If we have enough columns
                for i in range(1, len(data)):
                    table_style.add('ALIGN', (2, i), (3, i), 'RIGHT')  # Price columns
            
            table.setStyle(table_style)
            story.append(table)
            
        elif section.type == "footer":
            # Footer is handled by the canvas
            self.footer_text = section.text

def generate_styled_pdf(doc):
    """Generate a modern styled PDF with logo support"""
    # Create engine with modern position strategy
    engine = ModernDocumentEngine(position_strategy=ModernPositionStrategy())
    
    # Generate the PDF
    return engine.create_document_with_logo(doc)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Use command line argument as prompt
        prompt = " ".join(sys.argv[1:])
    else:
        # Use default example prompt
        prompt = "generate an invoice of a R2000.00 bike that was sold and a charge of R50 delivery fee and 14% of R2000.00 being the vat"
        print(f"Using default prompt: {prompt}")
    
    # Get invoice data from the SimpleInvoiceLLM
    llm = SimpleInvoiceLLM()
    invoice_data = llm.extract_invoice_data(prompt)
    doc = llm.generate_invoice_document(invoice_data)
    
    # Process with our styled engine
    pdf_bytes = generate_styled_pdf(doc)
    
    # Save PDF
    output_file = "styled_invoice.pdf"
    with open(output_file, "wb") as f:
        f.write(pdf_bytes)
    
    print(f"Modern styled invoice saved to {output_file}")

if __name__ == "__main__":
    main()
