# Installation

DocuForge is designed to be easy to install and use. Follow these instructions to get started with the library.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Standard Installation

Install DocuForge using pip:

```bash
pip install docuforge
```

## Development Installation

For development purposes, you can install DocuForge from the source code:

```bash
git clone https://github.com/yourusername/docuforge.git
cd docuforge
pip install -e ".[dev]"
```

## Dependencies

DocuForge relies on the following key dependencies:

- **ReportLab**: For PDF generation
- **fastapi**: For API functionality
- **pydantic**: For data validation
- **pillow**: For image processing

These dependencies will be installed automatically when you install DocuForge.

## Verifying Installation

To verify that DocuForge is installed correctly, you can run:

```bash
python -c "import docuforge; print(docuforge.__version__)"
```

## Optional Dependencies

For development and testing, you may want to install additional dependencies:

```bash
pip install "docuforge[dev]"  # Install development dependencies
pip install "docuforge[test]"  # Install testing dependencies
pip install "docuforge[docs]"  # Install documentation dependencies
```
