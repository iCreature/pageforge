# Usage Guide

This guide covers the basic and advanced usage patterns for PageForge.

## Basic Usage

### Creating a Simple Document

```python
from pageforge.core.models import DocumentData, Section
from pageforge.engines import generate_pdf

# Create document sections
sections = [
    Section(type="header", text="My First Document"),
    Section(type="paragraph", text="This is a simple document created with PageForge."),
    Section(type="paragraph", text="It demonstrates the basic capabilities of the library."),
    Section(type="footer", text="Page {page_number} of {total_pages}")
]

# Create document
doc = DocumentData(
    title="Simple Document",
    sections=sections
)

# Generate PDF
pdf_bytes = generate_pdf(doc)

# Save to file
with open("simple_document.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Adding a Logo

```python
from pageforge.core.models import DocumentData, Section, ImageData
from pageforge.engines import generate_pdf_with_logo

# Load logo
with open("path/to/logo.png", "rb") as f:
    logo_bytes = f.read()

# Create logo image
logo = ImageData(
    name="company_logo.png",
    data=logo_bytes,
    format="PNG"
)

# Create document
doc = DocumentData(
    title="Document with Logo",
    sections=[
        Section(type="header", text="Company Document"),
        Section(type="paragraph", text="This document includes our company logo."),
        Section(type="footer", text="Page {page_number} of {total_pages}")
    ],
    images=[logo]
)

# Generate PDF with logo
pdf_bytes = generate_pdf_with_logo(doc)

# Save to file
with open("logo_document.pdf", "wb") as f:
    f.write(pdf_bytes)
```

## Section Types

PageForge supports various section types for document content:

### Headers

```python
Section(type="header", text="Document Title")
```

Headers are rendered in a larger font and can be used for document titles and section headings.

### Paragraphs

```python
Section(type="paragraph", text="This is a paragraph of text that will be rendered with proper word wrapping.")
```

Paragraphs support standard text formatting and will automatically wrap to fit the page width.

### Tables

```python
table_data = [
    ["Name", "Age", "City"],
    ["John Doe", "32", "New York"],
    ["Jane Smith", "28", "London"],
    ["Bob Johnson", "45", "Paris"]
]

Section(type="table", rows=table_data)
```

Tables are rendered with proper column alignment and row styling.

### Lists

```python
list_items = [
    "First item",
    "Second item",
    "Third item with longer text that will wrap if needed"
]

Section(type="list", items=list_items)
```

Lists are rendered with bullet points and proper indentation.

### Footers

```python
Section(type="footer", text="Page {page_number} of {total_pages} - Confidential")
```

Footers appear at the bottom of each page. The placeholders `{page_number}` and `{total_pages}` will be replaced with the actual values.

## Command Line Interface

PageForge can be used from the command line:

```bash
# Generate a PDF from a JSON file containing document data
pageforge generate --input document_data.json --output result.pdf

# Generate a PDF with a logo
pageforge generate --input document_data.json --output result.pdf --logo company_logo.png
```

## API Usage

PageForge includes a FastAPI application that can be used to generate PDFs via HTTP:

```bash
# Start the API server
pageforge serve --host 0.0.0.0 --port 8000
```

Then send requests to the API:

```bash
# Generate a PDF (example with curl)
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d @document_data.json \
  --output result.pdf

# Generate a PDF with a logo
curl -X POST http://localhost:8000/generate-with-logo \
  -F "document=@document_data.json" \
  -F "logo=@company_logo.png" \
  --output result_with_logo.pdf
```
