Welcome to PageForge's documentation!
===================================

PageForge is an AI-powered document generation system that supports PDF creation with consistent logo placement and page numbering.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   introduction
   installation
   usage
   api
   examples
   contributing

Features
--------

* Generate professional PDFs with consistent styling
* Single logo support with flexible positioning
* Automatic page numbering in footers
* Support for tables, lists, and formatted text
* API for programmatic document generation
* CLI for command-line document creation
* Compatible with LLM-generated content

Installation
-----------

.. code-block:: bash

   pip install pageforge

Quick Start
----------

.. code-block:: python

   from pageforge.core.models import DocumentData, Section, ImageData
   from pageforge.engines import generate_pdf_with_logo
   
   # Create document structure
   doc = DocumentData(
       title="My Document",
       sections=[
           Section(type="header", text="Document Title"),
           Section(type="paragraph", text="This is a paragraph of text."),
           Section(type="footer", text="Page {page_number} of {total_pages}")
       ],
       images=[logo_image]  # Your logo as ImageData
   )
   
   # Generate PDF with logo
   pdf_bytes = generate_pdf_with_logo(doc)
   
   # Save the PDF
   with open("output.pdf", "wb") as f:
       f.write(pdf_bytes)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
