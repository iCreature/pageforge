from dataclasses import asdict, dataclass, field
from typing import Any, Optional

# Supported image formats for embedded images
SUPPORTED_IMAGE_FORMATS: set[str] = {"PNG", "JPG", "JPEG"}

# Allowed section types for document structure
ALLOWED_SECTION_TYPES: set[str] = {"table", "paragraph", "list", "header", "footer", "fragment", "heading"}

# Special section types with extended functionality
SPECIAL_SECTION_TYPES: set[str] = {"fragment", "template"}

@dataclass
class Section:
    """
    Represents a logical section of a document (table, paragraph, bullet list, header, etc.).
    
    A Section is the basic building block for document content. Each section has a specific type
    that determines how it will be rendered in the final PDF document.
    
    Special section types:
    - fragment: References a reusable document fragment by ID (stored in fragment_id)
    """
    type: str  # Type of section: "table", "paragraph", "list", "header", "footer", or "fragment"
    rows: Optional[list[list[Any]]] = None  # 2D list of data for tables, where each inner list is a row
    text: Optional[str] = None  # Text content for paragraphs, headers, and footers
    items: Optional[list[str]] = None  # List items for bullet/numbered lists
    data: dict[str, Any] = field(default_factory=dict)  # Additional metadata or styling information
    fragment_id: Optional[str] = None  # ID of a document fragment for type="fragment"
    level: Optional[int] = None  # Level for headers (h1, h2, h3, etc.)
    
    def __post_init__(self):
        if self.type not in ALLOWED_SECTION_TYPES:
            raise ValueError(f"Unsupported section type: {self.type}")
        
        # Initialize appropriate containers based on section type
        if self.type == "table" and self.rows is None:
            self.rows = []
        if self.type == "paragraph" and self.text is None:
            self.text = ""
        if self.type == "list" and self.items is None:
            self.items = []
            
        # Validate special section types
        if self.type == "fragment" and not self.fragment_id:
            raise ValueError("Fragment section requires a fragment_id")

    def to_dict(self):
        result = asdict(self)
        # Only include relevant fields based on section type
        if self.type == "paragraph" or self.type == "header" or self.type == "footer":
            result.pop("rows", None)
            result.pop("items", None)
        elif self.type == "table":
            result.pop("text", None)
            result.pop("items", None)
        elif self.type == "list":
            result.pop("rows", None)
            result.pop("text", None)
        elif self.type == "fragment":
            result.pop("rows", None)
            result.pop("text", None)
            result.pop("items", None)
        return result

@dataclass
class ImageData:
    """
    Represents an image to be embedded in the document.
    
    Images are stored as raw bytes and can be embedded at various locations in the document.
    The engine will handle proper placement and scaling of images within the PDF.    
    """
    name: str  # Unique identifier/name for the image
    data: bytes  # Raw binary image data
    format: str  # Image format (e.g., "PNG", "JPG", "JPEG")

    def __post_init__(self):
        fmt = self.format.upper()
        if fmt not in SUPPORTED_IMAGE_FORMATS:
            raise ValueError(f"Unsupported image format: {self.format}")
        self.format = fmt
        if not self.data or not isinstance(self.data, (bytes, bytearray)):
            raise ValueError("Image data must be non-empty bytes.")

    def to_dict(self):
        # Don't serialize raw bytes for LLMs, just length
        return {"name": self.name, "format": self.format, "data_length": len(self.data)}

@dataclass
class DocumentData:
    """
    Root document model for PageForge.
    
    This is the top-level container for all document content, including the title,
    sections (content), images, and additional metadata. This object is passed to the
    rendering engine to generate the final PDF document.
    
    This class can also reference a template by template_id, which allows for document
    reuse and standardization.
    """
    title: str  # Document title that appears in the header and metadata
    sections: list[Section] = field(default_factory=list)  # List of content sections in order of appearance
    images: list[ImageData] = field(default_factory=list)  # Images to embed in the document
    meta: dict[str, Any] = field(default_factory=dict)  # Additional metadata for document properties
    template_id: Optional[str] = None  # Optional template ID if this document uses a template
    template_values: dict[str, Any] = field(default_factory=dict)  # Values to fill in template placeholders
    style_data: dict[str, Any] = field(default_factory=dict)  # Document styling information
    
    def __post_init__(self):
        if not isinstance(self.sections, list):
            raise TypeError("sections must be a list")
        if not isinstance(self.images, list):
            raise TypeError("images must be a list")
        if not isinstance(self.template_values, dict):
            raise TypeError("template_values must be a dictionary")
        if not isinstance(self.style_data, dict):
            raise TypeError("style_data must be a dictionary")
    
    def add_section(self, section: Section) -> None:
        """Add a section to the document."""
        self.sections.append(section)
    
    def add_image(self, image: ImageData) -> None:
        """Add an image to the document."""
        self.images.append(image)
    
    def add_fragment(self, fragment_id: str) -> None:
        """Add a document fragment by ID."""
        fragment_section = Section(type="fragment", fragment_id=fragment_id)
        self.sections.append(fragment_section)
    
    def to_dict(self):
        result = {
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "images": [i.to_dict() for i in self.images],
            "meta": self.meta,
        }
        
        # Add template information if present
        if self.template_id:
            result["template_id"] = self.template_id
            result["template_values"] = self.template_values
            
        # Add style information if present
        if self.style_data:
            result["style_data"] = self.style_data
            
        return result
