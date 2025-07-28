"""
PageForge Templating Module
Contains template and fragment handling for document generation.
"""

# Import and expose public functions and classes from fragments module
from .fragments import (
    DocumentFragment,
    fragment_registry,
    get_fragment,
    register_fragment,
)

# Import and expose public functions and classes from templates module
from .templates import (
    DocumentTemplate,
    TemplatePlaceholder,
    get_template,
    register_template,
    template_registry,
)
