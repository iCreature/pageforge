"""
DocuForge Templating Module
Contains template and fragment handling for document generation.
"""

# Import and expose public functions and classes from fragments module
from .fragments import (
    DocumentFragment,
    fragment_registry,
    register_fragment,
    get_fragment,
)

# Import and expose public functions and classes from templates module
from .templates import (
    DocumentTemplate,
    TemplatePlaceholder,
    template_registry,
    register_template,
    get_template,
)
