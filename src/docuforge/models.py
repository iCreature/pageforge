from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Dict, Set

# Supported image formats for embedded images
SUPPORTED_IMAGE_FORMATS: Set[str] = {"PNG", "JPG", "JPEG"}

# Allowed section types for document structure
ALLOWED_SECTION_TYPES: Set[str] = {"table", "paragraph", "list", "header", "footer"}

@dataclass
class Section:
    """
    Represents a logical section of a document (table, paragraph, bullet list, header, etc.).
    
    A Section is the basic building block for document content. Each section has a specific type
    that determines how it will be rendered in the final PDF document.
    """
    type: str  # Type of section: "table", "paragraph", "list", "header", or "footer"
    rows: Optional[List[List[Any]]] = None  # 2D list of data for tables, where each inner list is a row
    text: Optional[str] = None  # Text content for paragraphs, headers, and footers
    items: Optional[List[str]] = None  # List items for bullet/numbered lists
    data: Dict[str, Any] = field(default_factory=dict)  # Additional metadata or styling information

    def __post_init__(self):
        if self.type not in ALLOWED_SECTION_TYPES:
            raise ValueError(f"Unsupported section type: {self.type}")
        if self.type == "table" and self.rows is None:
            self.rows = []
        if self.type == "paragraph" and self.text is None:
            self.text = ""
        if self.type == "list" and self.items is None:
            self.items = []

    def to_dict(self):
        return asdict(self)

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
    Root document model for DocuForge.
    
    This is the top-level container for all document content, including the title,
    sections (content), images, and additional metadata. This object is passed to the
    rendering engine to generate the final PDF document.
    """
    title: str  # Document title that appears in the header and metadata
    sections: List[Section] = field(default_factory=list)  # List of content sections in order of appearance
    images: List[ImageData] = field(default_factory=list)  # Images to embed in the document
    meta: Dict[str, Any] = field(default_factory=dict)  # Additional metadata for document properties

    def __post_init__(self):
        if not isinstance(self.sections, list):
            raise TypeError("sections must be a list")
        if not isinstance(self.images, list):
            raise TypeError("images must be a list")

    def to_dict(self):
        return {
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "images": [i.to_dict() for i in self.images],
            "meta": self.meta,
        }
