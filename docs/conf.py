"""
PageForge documentation configuration
"""
import os
import sys
import datetime

# Add the project root directory to the path so that autodoc can find the modules
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../src'))

# Project information
project = 'PageForge'
copyright = f'{datetime.datetime.now().year}, PageForge Team'
author = 'PageForge Team'

# The full version, including alpha/beta/rc tags
release = '0.1.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',       # Generate documentation from docstrings
    'sphinx.ext.viewcode',      # Add links to view the source code
    'sphinx.ext.napoleon',      # Support for NumPy and Google style docstrings
    'sphinx.ext.intersphinx',   # Link to other projects' documentation
    'sphinx.ext.coverage',      # Check documentation coverage
    'sphinx_autodoc_typehints', # Use type hints in documentation
    'myst_parser',              # Parse Markdown files
]

# Add any paths that contain templates here
templates_path = ['_templates']

# List of patterns to exclude from source files
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The theme to use for HTML and HTML Help pages
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files
html_static_path = ['_static']

# The master document
master_doc = 'index'

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'reportlab': ('https://www.reportlab.com/docs/reportlab-userguide.pdf', None),
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

# MyST parser settings
myst_enable_extensions = [
    'colon_fence',
    'deflist',
]

# Default code language for highlighting
highlight_language = 'python'

# Add a logo
# html_logo = "_static/logo.png"

# Show class and module docstrings
autoclass_content = 'both'
