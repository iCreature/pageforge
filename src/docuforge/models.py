from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Dict

SUPPORTED_IMAGE_FORMATS = {"PNG", "JPG", "JPEG"}
ALLOWED_SECTION_TYPES = {"table", "paragraph", "list", "header", "footer"}

@dataclass
class Section:
    """
    Represents a logical section of a document (table, paragraph, bullet list, header, etc.).
    """
    type: str
    rows: Optional[List[List[Any]]] = None
    text: Optional[str] = None
    items: Optional[List[str]] = None  # for bullet/numbered lists
    data: Dict[str, Any] = field(default_factory=dict)

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
    """
    name: str
    data: bytes
    format: str

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
    """
    title: str
    sections: List[Section] = field(default_factory=list)
    images: List[ImageData] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

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
