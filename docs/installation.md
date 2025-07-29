# Installation

PageForge is designed to be easy to install and use. Follow these instructions to get started with the library.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Standard Installation

Install PageForge using pip:

```bash
pip install pageforge
```

## Development Installation

For development purposes, you can install PageForge from the source code:

```bash
git clone https://github.com/yourusername/pageforge.git
cd pageforge
pip install -e ".[dev]"
```

## Dependencies

PageForge relies on the following key dependencies:

- **ReportLab**: For PDF generation
- **fastapi**: For API functionality
- **pydantic**: For data validation
- **pillow**: For image processing

These dependencies will be installed automatically when you install PageForge.

## Verifying Installation

To verify that PageForge is installed correctly, you can run:

```bash
python -c "import pageforge; print(pageforge.__version__)"
```

## Optional Dependencies

For development and testing, you may want to install additional dependencies:

```bash
pip install "pageforge[dev]"  # Install development dependencies
pip install "pageforge[test]"  # Install testing dependencies
pip install "pageforge[docs]"  # Install documentation dependencies
```
