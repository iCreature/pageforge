#!/usr/bin/env python3
"""
DocuForge AI Document Agent

This script provides an API for generating documents from user messages.
"""

import os
import json
import base64
import uvicorn
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Body, File, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from docuforge import generate_pdf
from docuforge.core.models import DocumentData, Section, ImageData
from docuforge.engines.reportlab_engine import ReportLabEngine
from io import BytesIO
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage

# Create a custom ReportLab engine that handles a single logo properly
class SingleLogoReportLabEngine(ReportLabEngine):
    """
    Custom ReportLab engine that displays a single logo in the top-right corner
    without generating synthetic test images
    """
    # Set default margin if not provided
    MARGIN = 36  # 0.5 inch in points
    
    def _render(self, doc: DocumentData) -> bytes:
        """Override the default render method to handle a single logo"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        # Create a BytesIO buffer for the PDF
        buffer = BytesIO()
        
        # Create the document with standard letter size
        document = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=self.MARGIN,
            leftMargin=self.MARGIN,
            topMargin=self.MARGIN,
            bottomMargin=self.MARGIN
        )
        
        # Build story (content flow)
        story = []
        styles = getSampleStyleSheet()
        
        # Add title
        if doc.title:
            story.append(Paragraph(doc.title, styles['Title']))
            story.append(Spacer(1, 12))
        
        # Process sections
        for section in doc.sections:
            stype = section.type
            
            # Check if section type is supported
            if stype not in ["paragraph", "table", "list", "header", "footer"]:
                raise ValueError(f"Unknown section type: {stype}")
                
            # Process section based on type
            if stype == "paragraph":
                story.append(Paragraph(section.text, styles['Normal']))
                story.append(Spacer(1, 6))
            elif stype == "header":
                story.append(Paragraph(section.text, styles['Heading1']))
                story.append(Spacer(1, 12))
            elif stype == "list":
                if hasattr(section, 'items') and section.items:
                    for item in section.items:
                        bullet_text = f"• {item}"
                        story.append(Paragraph(bullet_text, styles['Normal']))
                    story.append(Spacer(1, 6))
            elif stype == "table":
                if hasattr(section, 'rows') and section.rows:
                    from reportlab.platypus import Table, TableStyle
                    from reportlab.lib import colors
                    
                    table = Table(section.rows)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 12))
        
        # Logo handling for first page
        def first_page(canvas, doc):
            canvas.saveState()
            # Add logo if available
            if doc.images and len(doc.images) > 0:
                logo = doc.images[0]
                try:
                    # Create an in-memory image file
                    img_data = BytesIO(logo.data)
                    # Position logo at top-right corner
                    img = RLImage(img_data, width=1*inch, height=0.5*inch)
                    # Draw at the top-right corner with some padding
                    img.drawOn(canvas, letter[0] - 1.5*inch, letter[1] - 0.75*inch)
                except Exception as e:
                    print(f"Error rendering logo: {e}")
            canvas.restoreState()
        
        # Build the document with our custom page template
        document.build(story, onFirstPage=first_page, onLaterPages=first_page)
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

# Override the default generate_pdf function to use our custom engine
original_generate_pdf = generate_pdf

def custom_generate_pdf(doc: DocumentData) -> bytes:
    """Generate a PDF using our custom single logo engine"""
    print("Using custom PDF generator with logo support")
    # Use our custom engine
    engine = SingleLogoReportLabEngine()
    result = engine._render(doc)
    print(f"Generated PDF: {len(result)} bytes")
    return result

# Replace the default generate_pdf with our custom version
generate_pdf = custom_generate_pdf

# Create FastAPI app
app = FastAPI(title="DocuForge AI Agent", description="AI document generation agent using DocuForge")

class DocumentRequest(BaseModel):
    """Request model for document generation"""
    title: str
    content: str
    include_table: bool = False
    table_data: Optional[List[List[str]]] = None
    include_list: bool = False
    list_items: Optional[List[str]] = None
    author: str = "DocuForge User"
    include_logo: bool = False
    logo_data: Optional[str] = None  # Base64 encoded image data

class DocumentResponse(BaseModel):
    """Response model with document information"""
    filename: str
    size_kb: float
    message: str

def process_content(content: str) -> List[Section]:
    """Process user content into document sections"""
    sections = []
    
    # Split content into paragraphs
    paragraphs = content.split("\n\n")
    for paragraph in paragraphs:
        if paragraph.strip():
            sections.append(Section(type="paragraph", text=paragraph))
    
    return sections

@app.post("/generate-document", response_model=DocumentResponse)
def generate_document(request: DocumentRequest = Body(...)) -> DocumentResponse:
    """Generate a document based on user input"""
    try:
        # Start with content sections
        sections = process_content(request.content)
        
        # Add list if requested
        if request.include_list and request.list_items:
            sections.append(Section(type="paragraph", text="\nKey Points:"))
            sections.append(Section(type="list", items=request.list_items))
            
        # Add table if requested
        if request.include_table and request.table_data:
            sections.append(Section(type="paragraph", text="\nData Table:"))
            sections.append(Section(type="table", rows=request.table_data))
            
        # Add footer with author
        sections.append(Section(
            type="footer", 
            text=f"Generated by DocuForge v0.1.0 for {request.author} | Page {{page_number}} of {{total_pages}}"
        ))
        
        # Create document
        images = []
        if request.include_logo and request.logo_data:
            try:
                # Decode base64 image data
                logo_bytes = base64.b64decode(request.logo_data)
                # Create image data object
                logo = ImageData(
                    name="logo",
                    data=logo_bytes,
                    format="PNG"  # Assuming PNG format, adjust as needed
                )
                images.append(logo)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid logo data: {str(e)}")
        
        doc = DocumentData(
            title=request.title,
            sections=sections,
            images=images
        )
        
        # Generate PDF
        pdf_bytes = generate_pdf(doc)
        
        # Save to file
        filename = f"{request.title.replace(' ', '_')}.pdf"
        with open(filename, "wb") as f:
            f.write(pdf_bytes)
        
        # Return response
        size_kb = len(pdf_bytes) / 1024
        return DocumentResponse(
            filename=filename,
            size_kb=round(size_kb, 2),
            message=f"Document successfully generated! Size: {round(size_kb, 2)} KB"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")

@app.get("/")
async def root():
    """Welcome message"""
    return {
        "message": "Welcome to DocuForge AI Document Agent",
        "usage": "Send a POST request to /generate-document with title and content"
    }

@app.post("/generate-document-with-file")
async def generate_document_with_file(
    title: str = Form(...),
    content: str = Form(...),
    include_list: bool = Form(False),
    list_items: str = Form(""),
    include_table: bool = Form(False),
    table_data: str = Form(""),
    author: str = Form("DocuForge User"),
    logo: Optional[UploadFile] = File(None)
):
    """Generate a PDF document with an optional logo file upload"""
    
    # Prepare the request
    request = DocumentRequest(
        title=title,
        content=content,
        include_list=include_list,
        list_items=list_items.split(",") if list_items else None,
        include_table=include_table,
        table_data=[row.split(",") for row in table_data.split("\n") if row] if table_data else None,
        author=author,
        include_logo=logo is not None
    )
    
    # Handle logo if provided
    if logo:
        contents = await logo.read()
        request.logo_data = base64.b64encode(contents).decode('utf-8')
    
    # Generate the document
    result = generate_document(request)
    
    # Return the file directly
    return FileResponse(
        path=result.filename,
        media_type="application/pdf",
        filename=result.filename
    )

def main():
    """Run the API server"""
    print("Starting DocuForge AI Document Agent...")
    print("API Documentation available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DocuForge AI Document Agent")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode instead of API server")
    args = parser.parse_args()
    
    if args.cli:
        print("DocuForge AI Document Generator (CLI Mode)")
        
        title = input("Document title: ")
        print("Enter content (press Enter twice when done):")
        
        content_lines = []
        while True:
            line = input()
            if not line and content_lines and not content_lines[-1]:
                break
            content_lines.append(line)
        
        content = "\n".join(content_lines)
        
        include_list = input("Include a bullet list? (y/n): ").lower() == 'y'
        list_items = []
        if include_list:
            print("Enter list items (one per line, empty line to finish):")
            while True:
                item = input("- ")
                if not item:
                    break
                list_items.append(item)
        
        include_table = input("Include a table? (y/n): ").lower() == 'y'
        table_data = []
        if include_table:
            print("Enter table header (comma separated values):")
            header = input().split(",")
            table_data.append([h.strip() for h in header])
            
            print("Enter table rows (comma separated values, empty line to finish):")
            while True:
                row = input()
                if not row:
                    break
                table_data.append([cell.strip() for cell in row.split(",")])
        
        include_logo = input("Include a logo? (y/n): ").lower() == 'y'
        logo_data = None
        if include_logo:
            logo_path = input("Enter logo file path: ")
            try:
                with open(logo_path, "rb") as f:
                    logo_bytes = f.read()
                    logo_data = base64.b64encode(logo_bytes).decode('utf-8')
            except Exception as e:
                print(f"Error reading logo file: {e}")
                include_logo = False
        
        author = input("Author name (press Enter for default): ")
        
        request = DocumentRequest(
            title=title,
            content=content,
            include_list=include_list,
            list_items=list_items if include_list else None,
            include_table=include_table,
            table_data=table_data if include_table else None,
            author=author if author else "DocuForge User",
            include_logo=include_logo,
            logo_data=logo_data if include_logo else None
        )
        
        # Create document
        try:
            sections = process_content(request.content)
            
            if request.include_list and request.list_items:
                sections.append(Section(type="paragraph", text="\nKey Points:"))
                sections.append(Section(type="list", items=request.list_items))
                
            if request.include_table and request.table_data:
                sections.append(Section(type="paragraph", text="\nData Table:"))
                sections.append(Section(type="table", rows=request.table_data))
                
            sections.append(Section(
                type="footer", 
                text=f"Generated by DocuForge v0.1.0 for {request.author} | Page {{page_number}} of {{total_pages}}"
            ))
            
            doc = DocumentData(
                title=request.title,
                sections=sections
            )
            
            # Generate PDF
            print("Generating PDF...")
            pdf_bytes = generate_pdf(doc)
            
            # Save to file
            filename = f"{request.title.replace(' ', '_')}.pdf"
            with open(filename, "wb") as f:
                f.write(pdf_bytes)
            
            size_kb = len(pdf_bytes) / 1024
            print(f"Document successfully generated and saved as {filename}")
            print(f"PDF size: {round(size_kb, 2)} KB")
            
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        main()
