#!/usr/bin/env python3
"""
Minimalistic Invoice Generator
This script creates basic invoices from natural language prompts with minimal dependencies
"""
import os
import re
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any
from io import BytesIO

# ReportLab imports - only the essentials
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

@dataclass
class InvoiceItem:
    """Simple invoice item"""
    name: str
    quantity: int
    price: float
    
    @property
    def total(self) -> float:
        return self.quantity * self.price

@dataclass
class Invoice:
    """Simple invoice data"""
    invoice_number: str
    date: str
    customer_name: str
    items: List[InvoiceItem]
    vat_rate: float
    delivery_fee: float
    
    @property
    def subtotal(self) -> float:
        return sum(item.total for item in self.items)
    
    @property
    def vat_amount(self) -> float:
        return self.subtotal * self.vat_rate
    
    @property
    def total(self) -> float:
        return self.subtotal + self.vat_amount + self.delivery_fee

def extract_invoice_data(prompt: str) -> Invoice:
    """Extract invoice data from a prompt using simple regex patterns"""
    # Default values
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-001"
    date = datetime.now().strftime("%Y-%m-%d")
    customer_name = "Customer"
    items = []
    vat_rate = 0.14  # Default VAT rate
    delivery_fee = 0
    
    # Extract amounts using regex
    amounts = re.findall(r"R(\d+(?:\.\d+)?)", prompt)
    if len(amounts) >= 2:
        item_price = float(amounts[0])
        delivery_fee = float(amounts[1])
        
    # Extract VAT percentage
    vat_match = re.search(r"(\d+)%", prompt)
    if vat_match:
        vat_rate = float(vat_match.group(1)) / 100
    
    # Extract item description
    item_match = re.search(r"([\w\s]+) (?:that|which) was sold", prompt)
    if item_match:
        item_name = item_match.group(1).strip()
        items.append(InvoiceItem(name=item_name, quantity=1, price=item_price))
    
    # Create invoice
    return Invoice(
        invoice_number=invoice_number,
        date=date,
        customer_name=customer_name,
        items=items,
        vat_rate=vat_rate,
        delivery_fee=delivery_fee
    )

def create_minimal_invoice_pdf(invoice: Invoice) -> bytes:
    """Create a minimal invoice PDF"""
    buffer = BytesIO()
    
    # Create canvas
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Set font
    c.setFont("Helvetica-Bold", 16)
    
    # Draw title
    c.drawString(2*cm, height - 2*cm, f"Invoice #{invoice.invoice_number}")
    
    # Draw date and customer info
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 3*cm, f"Date: {invoice.date}")
    c.drawString(2*cm, height - 3.5*cm, f"Customer: {invoice.customer_name}")
    
    # Draw items table
    data = [["Item", "Quantity", "Price", "Total"]]
    for item in invoice.items:
        data.append([
            item.name, 
            str(item.quantity), 
            f"R{item.price:.2f}", 
            f"R{item.total:.2f}"
        ])
    
    table = Table(data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    
    table.wrapOn(c, width, height)
    table.drawOn(c, 2*cm, height - 8*cm)
    
    # Draw totals
    y_position = height - 10*cm
    c.setFont("Helvetica", 12)
    c.drawString(12*cm, y_position, f"Subtotal: R{invoice.subtotal:.2f}")
    
    y_position -= 0.7*cm
    c.drawString(12*cm, y_position, 
                f"VAT ({invoice.vat_rate*100:.0f}%): R{invoice.vat_amount:.2f}")
    
    y_position -= 0.7*cm
    c.drawString(12*cm, y_position, f"Delivery: R{invoice.delivery_fee:.2f}")
    
    y_position -= 1*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(12*cm, y_position, f"Total: R{invoice.total:.2f}")
    
    # Draw footer
    c.setFont("Helvetica", 10)
    c.drawString(width/2 - 4*cm, 1*cm, "Thank you for your business!")
    c.drawString(width - 7*cm, 0.5*cm, f"Page 1 of 1")
    
    # Finalize the PDF
    c.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def process_prompt(prompt: str) -> bytes:
    """Process a prompt and generate an invoice PDF"""
    # Extract invoice data from prompt
    invoice = extract_invoice_data(prompt)
    
    # Generate PDF
    return create_minimal_invoice_pdf(invoice)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Use command line argument as prompt
        prompt = " ".join(sys.argv[1:])
    else:
        # Use default example prompt
        prompt = "generate an invoice of a R2000.00 bike that was sold and a charge of R50 delivery fee and 14% of R2000.00 being the vat"
        print(f"Using default prompt: {prompt}")
    
    # Process prompt and generate PDF
    pdf_bytes = process_prompt(prompt)
    
    # Save PDF
    output_file = "minimal_invoice.pdf"
    with open(output_file, "wb") as f:
        f.write(pdf_bytes)
    
    print(f"Minimal invoice saved to {output_file}")

if __name__ == "__main__":
    main()
