# Code Examples

This page contains practical examples of using PageForge in various scenarios.

## Basic Invoice Example

Create a simple invoice document:

```python
from pageforge.core.models import DocumentData, Section
from pageforge.engines import generate_pdf

# Define invoice data
invoice_number = "INV-2025-0719"
customer = "Acme Corporation"
items = [
    {"name": "Product A", "quantity": 2, "price": 50.00},
    {"name": "Product B", "quantity": 1, "price": 75.00},
    {"name": "Service X", "quantity": 5, "price": 100.00}
]

# Calculate totals
subtotal = sum(item["quantity"] * item["price"] for item in items)
vat = subtotal * 0.14  # 14% VAT
total = subtotal + vat

# Create document sections
sections = [
    # Header
    Section(type="header", text=f"Invoice #{invoice_number}"),
    
    # Customer info
    Section(type="paragraph", text=f"Customer: {customer}\nDate: 2025-07-19"),
    
    # Items table
    Section(
        type="table", 
        rows=[
            ["Item", "Quantity", "Unit Price", "Total"],
            *[[
                item["name"],
                str(item["quantity"]),
                f"R{item['price']:.2f}",
                f"R{item['quantity'] * item['price']:.2f}"
            ] for item in items]
        ]
    ),
    
    # Totals
    Section(
        type="paragraph", 
        text=f"Subtotal: R{subtotal:.2f}\nVAT (14%): R{vat:.2f}\nTotal: R{total:.2f}"
    ),
    
    # Footer
    Section(type="footer", text="Page {page_number} of {total_pages}")
]

# Create document
doc = DocumentData(
    title=f"Invoice #{invoice_number}",
    sections=sections
)

# Generate PDF
pdf_bytes = generate_pdf(doc)

# Save to file
with open("invoice_example.pdf", "wb") as f:
    f.write(pdf_bytes)
```

## Report with Logo

Generate a report with a company logo:

```python
from pageforge.core.models import DocumentData, Section, ImageData
from pageforge.engines import generate_pdf_with_logo
import base64

# Load logo from file
with open("company_logo.png", "rb") as f:
    logo_bytes = f.read()

# Create logo image
logo = ImageData(
    name="company_logo.png",
    data=logo_bytes,
    format="PNG"
)

# Create document sections
sections = [
    # Header
    Section(type="header", text="Quarterly Financial Report"),
    
    # Introduction
    Section(
        type="paragraph", 
        text="This report summarizes the financial performance for Q2 2025."
    ),
    
    # Executive summary
    Section(type="header", text="Executive Summary"),
    Section(
        type="paragraph",
        text="The company has exceeded its quarterly targets by 15%, with strong performance in the technology sector."
    ),
    
    # Financial highlights
    Section(type="header", text="Financial Highlights"),
    Section(
        type="table",
        rows=[
            ["Metric", "Q1 2025", "Q2 2025", "Change"],
            ["Revenue", "R5.2M", "R6.3M", "+21%"],
            ["Expenses", "R3.8M", "R4.1M", "+8%"],
            ["Net Profit", "R1.4M", "R2.2M", "+57%"],
            ["Profit Margin", "27%", "35%", "+8%"]
        ]
    ),
    
    # Recommendations
    Section(type="header", text="Recommendations"),
    Section(
        type="list",
        items=[
            "Increase investment in the technology division by 20%",
            "Expand marketing efforts in the EMEA region",
            "Accelerate hiring for software development roles",
            "Consider strategic acquisitions in the AI space"
        ]
    ),
    
    # Footer
    Section(type="footer", text="Confidential - Page {page_number} of {total_pages}")
]

# Create document
doc = DocumentData(
    title="Quarterly Financial Report",
    sections=sections,
    images=[logo]
)

# Generate PDF with logo
pdf_bytes = generate_pdf_with_logo(doc)

# Save to file
with open("financial_report.pdf", "wb") as f:
    f.write(pdf_bytes)
```

## LLM Integration Example

This example demonstrates integrating PageForge with an LLM to generate content:

```python
import os
import requests
from pageforge.core.models import DocumentData, Section, ImageData
from pageforge.engines import generate_pdf_with_logo

def get_llm_generated_content(prompt):
    """Get content from an LLM API based on a prompt"""
    # Replace with your actual LLM API call
    api_key = os.environ.get("LLM_API_KEY")
    
    response = requests.post(
        "https://api.llm-provider.com/generate",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"prompt": prompt, "max_tokens": 500}
    )
    
    return response.json()["content"]

def create_invoice_from_prompt(prompt):
    """Create an invoice based on natural language prompt"""
    # Get structured data from LLM
    llm_response = get_llm_generated_content(
        f"Extract invoice data from this prompt: '{prompt}'. "
        "Return a JSON object with invoice_number, date, customer_name, "
        "items (array of name, quantity, price objects), vat_rate, and delivery_fee."
    )
    
    # Parse LLM response (simplified for example)
    import json
    invoice_data = json.loads(llm_response)
    
    # Calculate totals
    subtotal = sum(item["price"] * item["quantity"] for item in invoice_data["items"])
    vat = subtotal * invoice_data["vat_rate"]
    total = subtotal + vat + invoice_data["delivery_fee"]
    
    # Create document sections
    sections = [
        # Header
        Section(type="header", text=f"Invoice #{invoice_data['invoice_number']}"),
        
        # Customer info
        Section(
            type="paragraph", 
            text=f"Customer: {invoice_data['customer_name']}\nDate: {invoice_data['date']}"
        ),
        
        # Items table
        Section(
            type="table", 
            rows=[
                ["Item", "Quantity", "Unit Price", "Total"],
                *[[
                    item["name"],
                    str(item["quantity"]),
                    f"R{item['price']:.2f}",
                    f"R{item['quantity'] * item['price']:.2f}"
                ] for item in invoice_data["items"]]
            ]
        ),
        
        # Totals
        Section(
            type="paragraph", 
            text=(
                f"Subtotal: R{subtotal:.2f}\n"
                f"VAT ({invoice_data['vat_rate']*100:.0f}%): R{vat:.2f}\n"
                f"Delivery Fee: R{invoice_data['delivery_fee']:.2f}\n"
                f"Total: R{total:.2f}"
            )
        ),
        
        # Footer
        Section(type="footer", text="Page {page_number} of {total_pages}")
    ]
    
    # Load default logo
    with open("default_logo.png", "rb") as f:
        logo_bytes = f.read()
    
    logo = ImageData(
        name="default_logo.png",
        data=logo_bytes,
        format="PNG"
    )
    
    # Create document
    doc = DocumentData(
        title=f"Invoice #{invoice_data['invoice_number']}",
        sections=sections,
        images=[logo]
    )
    
    return doc

# Usage
prompt = "Generate an invoice for a R2000.00 bike that was sold with a charge of R50 delivery fee and 14% VAT"
doc = create_invoice_from_prompt(prompt)
pdf_bytes = generate_pdf_with_logo(doc)

with open("llm_generated_invoice.pdf", "wb") as f:
    f.write(pdf_bytes)
```

## API Server Example

This example shows how to set up and use the PageForge API server:

```python
# server.py
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
import uvicorn
import json
from pageforge.core.models import DocumentData, Section, ImageData
from pageforge.engines import generate_pdf, generate_pdf_with_logo

app = FastAPI(title="PageForge API")

@app.post("/generate")
async def generate_document(document: dict):
    """Generate a PDF from document data"""
    try:
        # Convert to DocumentData
        sections = [
            Section(
                type=section["type"],
                text=section.get("text", ""),
                items=section.get("items"),
                rows=section.get("rows")
            ) for section in document["sections"]
        ]
        
        doc = DocumentData(
            title=document["title"],
            sections=sections
        )
        
        # Generate PDF
        pdf_bytes = generate_pdf(doc)
        
        # Return PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={document['title']}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-with-logo")
async def generate_document_with_logo(
    document: str = Form(...),
    logo: UploadFile = File(...)
):
    """Generate a PDF with a logo"""
    try:
        # Parse document JSON
        doc_data = json.loads(document)
        
        # Read logo
        logo_bytes = await logo.read()
        logo_format = logo.filename.split(".")[-1].upper()
        
        # Convert to DocumentData with logo
        sections = [
            Section(
                type=section["type"],
                text=section.get("text", ""),
                items=section.get("items"),
                rows=section.get("rows")
            ) for section in doc_data["sections"]
        ]
        
        logo_image = ImageData(
            name=logo.filename,
            data=logo_bytes,
            format=logo_format
        )
        
        doc = DocumentData(
            title=doc_data["title"],
            sections=sections,
            images=[logo_image]
        )
        
        # Generate PDF with logo
        pdf_bytes = generate_pdf_with_logo(doc)
        
        # Return PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={doc_data['title']}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Usage with curl:

```bash
# Generate a basic document
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d @document_data.json \
  --output result.pdf

# Generate a document with logo
curl -X POST http://localhost:8000/generate-with-logo \
  -F "document=@document_data.json" \
  -F "logo=@logo.png" \
  --output result_with_logo.pdf
```
