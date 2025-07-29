# API Reference

This section provides detailed information about the PageForge API components.

## Core Models

### DocumentData

`DocumentData` is the main container for document content.

```python
class DocumentData:
    title: str
    sections: List[Section]
    images: Optional[List[ImageData]] = None
```

**Parameters:**
- `title`: The document title
- `sections`: List of content sections (paragraphs, tables, etc.)
- `images`: Optional list of images, including the logo

### Section

`Section` represents a content block within a document.

```python
class Section:
    type: str
    text: str = ""
    items: Optional[List[str]] = None
    rows: Optional[List[List[str]]] = None
```

**Parameters:**
- `type`: The section type ("header", "paragraph", "table", "list", "footer")
- `text`: Text content for paragraph, header, and footer sections
- `items`: List items for "list" type sections
- `rows`: Table data for "table" type sections

### ImageData

`ImageData` contains image binary data and metadata.

```python
class ImageData:
    name: str
    data: bytes
    format: str
```

**Parameters:**
- `name`: Image filename
- `data`: Binary image data
- `format`: Image format ("PNG", "JPG", "JPEG")

## Document Generation

### generate_pdf

Generate a PDF document from `DocumentData`.

```python
def generate_pdf(doc: DocumentData) -> bytes:
    """
    Generate a PDF document from DocumentData.
    
    Args:
        doc: Document data including content sections
        
    Returns:
        bytes: The generated PDF as bytes
    """
```

### generate_pdf_with_logo

Generate a PDF document with a logo from `DocumentData`.

```python
def generate_pdf_with_logo(doc: DocumentData) -> bytes:
    """
    Generate a PDF document with a logo from DocumentData.
    
    Args:
        doc: Document data including content sections and logo image
        
    Returns:
        bytes: The generated PDF as bytes
    """
```

## Logo Handling

### LogoHandler

`LogoHandler` provides logo validation and processing.

```python
class LogoHandler:
    @staticmethod
    def validate_logo(logo_data: ImageData) -> bool:
        """
        Validate logo format and size.
        
        Args:
            logo_data: Logo image data
            
        Returns:
            bool: True if valid, False otherwise
        """
    
    @staticmethod
    def process_logo_data(logo_data: bytes, format_name: str) -> ImageData:
        """
        Process raw logo data into ImageData.
        
        Args:
            logo_data: Raw logo binary data
            format_name: Image format name
            
        Returns:
            ImageData: Processed logo data
        """
```

## Logo Positioning

### LogoPositionStrategy

`LogoPositionStrategy` is an interface for logo positioning strategies.

```python
class LogoPositionStrategy:
    def position_logo(self, canvas, page_size, img, width, height):
        """
        Position the logo on the canvas.
        
        Args:
            canvas: ReportLab canvas
            page_size: Page dimensions (width, height)
            img: ReportLab Image object
            width: Logo width
            height: Logo height
        """
```

### TopRightCornerStrategy

`TopRightCornerStrategy` positions logos in the top-right corner of the page.

```python
class TopRightCornerStrategy(LogoPositionStrategy):
    def position_logo(self, canvas, page_size, img, width, height):
        """
        Position the logo at the top right of the page.
        
        Args:
            canvas: ReportLab canvas
            page_size: Page dimensions (width, height)
            img: ReportLab Image object
            width: Logo width
            height: Logo height
        """
```

## Document Engine

### LogoDocumentEngine

`LogoDocumentEngine` generates PDFs with logos.

```python
class LogoDocumentEngine:
    def __init__(self, position_strategy=None):
        """
        Initialize with a positioning strategy for logo placement.
        
        Args:
            position_strategy: Strategy for logo positioning
        """
    
    def create_document_with_logo(self, doc):
        """
        Create a PDF document with a logo.
        
        Args:
            doc: The document data including content and optional logo
            
        Returns:
            bytes: The generated PDF
        """
```

## Page Numbering

### NumberedCanvas

`NumberedCanvas` extends ReportLab's Canvas to add page numbering.

```python
class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        """Initialize the numbered canvas"""
    
    def showPage(self):
        """Save page state before showing the page"""
    
    def save(self):
        """Add page numbers to each page and save the document"""
    
    def draw_page_number(self, page_count):
        """Draw the page number on the current page"""
```

## CLI Interface

```bash
# Display help
pageforge --help

# Generate PDF
pageforge generate --input INPUT_FILE --output OUTPUT_FILE [--logo LOGO_FILE]
```

## API Endpoints

### `/generate`

Generate a PDF from document data.

- **Method**: POST
- **Content-Type**: application/json
- **Request Body**: DocumentData JSON
- **Response**: PDF file

### `/generate-with-logo`

Generate a PDF with a logo.

- **Method**: POST
- **Content-Type**: multipart/form-data
- **Form Fields**:
  - `document`: DocumentData JSON
  - `logo`: Logo image file
- **Response**: PDF file
