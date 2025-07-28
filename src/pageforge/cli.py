#!/usr/bin/env python
"""PageForge CLI - Command Line Interface for PageForge PDF generation."""

import argparse
import json
import sys
from importlib.metadata import version
from pathlib import Path

from pageforge.api import generate_pdf, generate_pdf_with_logo
from pageforge.core.models import DocumentData


def main():
    """Main CLI entrypoint for PageForge."""
    parser = argparse.ArgumentParser(description="PageForge PDF generation CLI")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    parser.add_argument(
        "--from-json", 
        type=Path, 
        help="Generate PDF from JSON spec file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output.pdf"),
        help="Output PDF filename (default: output.pdf)"
    )
    parser.add_argument(
        "--logo",
        type=Path,
        help="Path to logo image file (optional)"
    )
    
    args = parser.parse_args()
    
    if args.version:
        print("pageforge", version("pageforge"))
        return 0
    
    if args.from_json:
        try:
            with open(args.from_json) as f:
                data = json.load(f)
            
            # Create DocumentData from JSON
            doc_data = DocumentData.from_dict(data)
            
            # Generate PDF with or without logo
            if args.logo and args.logo.exists():
                with open(args.logo, 'rb') as logo_file:
                    logo_file.read()
                    pdf_bytes = generate_pdf_with_logo(
                        doc_data, 
                        logo_path=args.logo
                    )
            else:
                pdf_bytes = generate_pdf(doc_data)
            
            # Write to output file
            with open(args.output, 'wb') as f:
                f.write(pdf_bytes)
            
            print(f"PDF generated successfully: {args.output}")
            return 0
        
        except Exception as e:
            print(f"Error generating PDF: {str(e)}", file=sys.stderr)
            return 1
    
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
