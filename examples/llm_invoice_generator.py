#!/usr/bin/env python3
"""
LLM-powered Invoice Generator
This script simulates an LLM generating invoices from natural language prompts.
"""
import os
import re
import sys
import random
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Tuple, Any

# Import PageForge components
from pageforge import (
    DocumentData, Section, ImageData, 
    generate_pdf_with_logo, LogoHandler
)

class SimpleInvoiceLLM:
    """A simple LLM that extracts invoice details from prompts"""
    
    def __init__(self):
        """Initialize the LLM"""
        self.default_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_logo.png")
        self.create_default_logo_if_needed()
    
    def create_default_logo_if_needed(self):
        """Create a default logo if it doesn't exist"""
        if not os.path.exists(self.default_logo_path):
            try:
                # Create a simple default logo using Python's standard library
                from PIL import Image, ImageDraw, ImageFont
                
                # Create a blank image with white background
                img = Image.new('RGB', (200, 100), color=(255, 255, 255))
                d = ImageDraw.Draw(img)
                
                # Draw text
                try:
                    font = ImageFont.truetype("Arial", 24)
                except IOError:
                    font = ImageFont.load_default()
                
                d.text((10, 10), "PageForge", fill=(0, 0, 0), font=font)
                d.text((10, 50), "Invoice", fill=(0, 0, 0), font=font)
                
                # Save the image
                img.save(self.default_logo_path)
                print(f"Created default logo at {self.default_logo_path}")
            except ImportError:
                # If PIL is not available, create an empty PNG file
                with open(self.default_logo_path, 'wb') as f:
                    # Minimal valid PNG file
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
                print(f"Created empty default logo at {self.default_logo_path}")
    
    def get_logo_data(self) -> ImageData:
        """Get the logo data"""
        with open(self.default_logo_path, 'rb') as f:
            logo_data = f.read()
        
        return ImageData(
            name="logo.png",
            data=logo_data,
            format="PNG"
        )
    
    def extract_invoice_data(self, prompt: str) -> Dict[str, Any]:
        """Extract invoice data from prompt using regex patterns
        
        This simulates what a real LLM would do with more sophisticated NLP
        """
        data = {
            "items": [],
            "total": 0,
            "vat_rate": 0.14,  # Default VAT rate
            "vat_amount": 0,
            "delivery_fee": 0,
            "invoice_number": f"INV-{random.randint(10000, 99999)}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "customer": "Customer",
            "seller": "PageForge Enterprises",
        }
        
        # Extract amounts with regex
        amounts = re.findall(r"R(\d+(?:\.\d+)?)", prompt)
        if len(amounts) >= 3:
            # Assume the first is the item price, second is delivery, third is VAT percentage
            item_price = float(amounts[0])
            data["delivery_fee"] = float(amounts[1])
            
            # Try to extract VAT percentage
            vat_match = re.search(r"(\d+)%", prompt)
            if vat_match:
                data["vat_rate"] = float(vat_match.group(1)) / 100
        
        # Extract item descriptions
        item_match = re.search(r"([\w\s]+) (?:that|which) was sold", prompt)
        if item_match:
            item_name = item_match.group(1).strip()
            data["items"].append({
                "name": item_name,
                "price": item_price,
                "quantity": 1
            })
        
        # Calculate VAT and totals
        subtotal = sum(item["price"] * item["quantity"] for item in data["items"])
        data["vat_amount"] = subtotal * data["vat_rate"]
        data["total"] = subtotal + data["vat_amount"] + data["delivery_fee"]
        
        return data
    
    def generate_invoice_document(self, invoice_data: Dict[str, Any]) -> DocumentData:
        """Generate a DocumentData object from invoice data"""
        title = f"Invoice #{invoice_data['invoice_number']}"
        
        # Create header information section
        header_text = (
            f"Invoice Date: {invoice_data['date']}\n"
            f"Invoice #: {invoice_data['invoice_number']}\n\n"
            f"Seller: {invoice_data['seller']}\n"
            f"Customer: {invoice_data['customer']}\n"
        )
        
        # Create items table
        table_rows = [["Item", "Quantity", "Price", "Total"]]
        for item in invoice_data["items"]:
            item_total = item["price"] * item["quantity"]
            table_rows.append([
                item["name"],
                str(item["quantity"]),
                f"R{item['price']:.2f}",
                f"R{item_total:.2f}"
            ])
        
        # Create summary section
        subtotal = sum(item["price"] * item["quantity"] for item in invoice_data["items"])
        summary_text = (
            f"Subtotal: R{subtotal:.2f}\n"
            f"VAT ({invoice_data['vat_rate']*100:.0f}%): R{invoice_data['vat_amount']:.2f}\n"
            f"Delivery Fee: R{invoice_data['delivery_fee']:.2f}\n"
            f"Total: R{invoice_data['total']:.2f}"
        )
        
        # Create thank you note
        thank_you_text = (
            "Thank you for your business!\n"
            "Payment due within 30 days of receipt."
        )
        
        # Create sections
        sections = [
            Section(type="header", text=title),
            Section(type="paragraph", text=header_text),
            Section(type="paragraph", text="Invoice Items:"),
            Section(type="table", rows=table_rows),
            Section(type="paragraph", text=summary_text),
            Section(type="paragraph", text=thank_you_text),
            Section(type="footer", text="Page {page_number} of {total_pages} - Generated by PageForge")
        ]
        
        # Create and return document
        return DocumentData(
            title=title,
            sections=sections,
            images=[self.get_logo_data()]
        )

def process_prompt(prompt: str) -> bytes:
    """Process a prompt and return a PDF document"""
    # Create LLM instance
    llm = SimpleInvoiceLLM()
    
    # Extract invoice data from prompt
    invoice_data = llm.extract_invoice_data(prompt)
    
    # Generate document from invoice data
    doc = llm.generate_invoice_document(invoice_data)
    
    # Generate PDF
    pdf_bytes = generate_pdf_with_logo(doc)
    
    return pdf_bytes

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Use command line argument as prompt
        prompt = " ".join(sys.argv[1:])
    else:
        # Use default example prompt
        prompt = "generate an invoice of a R2000.00 bike that was sold and a charge of R50 delivery fee and 14% of R2000.00 being the vat"
        print(f"Using default prompt: {prompt}")
    
    # Process prompt
    pdf_bytes = process_prompt(prompt)
    
    # Save PDF
    output_file = "llm_generated_invoice.pdf"
    with open(output_file, "wb") as f:
        f.write(pdf_bytes)
    
    print(f"Invoice saved to {output_file}")

if __name__ == "__main__":
    main()
