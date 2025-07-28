import uuid
from typing import Any, Optional, Union

from ..utils.logging_config import get_logger
from .models import DocumentData, ImageData, Section


class DocumentBuilder:
    """
    Builder for stepwise, agent-friendly construction of DocumentData.
    
    This class provides a fluent interface for building DocumentData objects,
    allowing step-by-step addition of document components like sections,
    images, and metadata.
    
    Attributes:
        _title: The document title
        _sections: List of document sections
        _images: List of document images
        _meta: Dictionary of document metadata
        logger: Logger for builder operations
        builder_id: Unique identifier for this builder instance
    """
    def __init__(self):
        self._title: Optional[str] = None
        self._sections: list[Section] = []
        self._images: list[ImageData] = []
        self._meta: dict[str, Any] = {}
        self.builder_id = str(uuid.uuid4())[:8]
        self.logger = get_logger("pageforge.builder", {"builder_id": self.builder_id})
        self.logger.debug(f"Created new DocumentBuilder instance (ID: {self.builder_id})")

    def set_title(self, title: str):
        """
        Set the document title.
        
        Args:
            title: The title for the document
            
        Returns:
            Self for method chaining
        """
        self._title = title
        self.logger.debug(f"Set document title: '{title}'")
        return self

    def add_section(self, section: Union[Section, dict[str, Any]]):
        """
        Add a section to the document.
        
        Args:
            section: A Section object or a dictionary with section fields
            
        Returns:
            Self for method chaining
            
        Raises:
            TypeError: If the section is not a Section object or a dictionary
        """
        try:
            if isinstance(section, dict):
                self.logger.debug(f"Converting section dictionary to Section object: {section.get('type', 'unknown')}")
                section = Section(**{k: v for k, v in section.items() if k in Section.__dataclass_fields__})
            if not isinstance(section, Section):
                self.logger.error(f"Invalid section type: {type(section).__name__}")
                raise TypeError("section must be Section or dict")
                
            section_type = getattr(section, "type", "unknown")
            self._sections.append(section)
            self.logger.info(f"Added section: {section_type} (total sections: {len(self._sections)})")
            return self
        except Exception as e:
            self.logger.error(f"Error adding section: {str(e)}")
            raise

    def add_sections(self, sections: list[Union[Section, dict[str, Any]]]):
        """
        Add multiple sections to the document.
        
        Args:
            sections: A list of Section objects or dictionaries
            
        Returns:
            Self for method chaining
        """
        self.logger.debug(f"Adding multiple sections: {len(sections)}")
        for s in sections:
            self.add_section(s)
        self.logger.info(f"Added {len(sections)} sections (total: {len(self._sections)})")
        return self

    def add_image(self, image: Union[ImageData, dict[str, Any]]):
        """
        Add an image to the document.
        
        Args:
            image: An ImageData object or a dictionary with image fields
            
        Returns:
            Self for method chaining
            
        Raises:
            TypeError: If the image is not an ImageData object or a dictionary
        """
        try:
            if isinstance(image, dict):
                self.logger.debug(f"Converting image dictionary to ImageData object: {image.get('name', 'unnamed')}")
                image = ImageData(**{k: v for k, v in image.items() if k in ImageData.__dataclass_fields__})
            if not isinstance(image, ImageData):
                self.logger.error(f"Invalid image type: {type(image).__name__}")
                raise TypeError("image must be ImageData or dict")
                
            image_name = getattr(image, "name", "unnamed")
            image_size = len(getattr(image, "data", b""))
            self._images.append(image)
            self.logger.info(f"Added image: {image_name} ({image_size} bytes, total images: {len(self._images)})")
            return self
        except Exception as e:
            self.logger.error(f"Error adding image: {str(e)}")
            raise

    def add_images(self, images: list[Union[ImageData, dict[str, Any]]]):
        """
        Add multiple images to the document.
        
        Args:
            images: A list of ImageData objects or dictionaries
            
        Returns:
            Self for method chaining
        """
        self.logger.debug(f"Adding multiple images: {len(images)}")
        for img in images:
            self.add_image(img)
        self.logger.info(f"Added {len(images)} images (total: {len(self._images)})")
        return self

    def set_meta(self, meta: dict[str, Any]):
        """
        Set document metadata.
        
        Args:
            meta: Dictionary of metadata key-value pairs
            
        Returns:
            Self for method chaining
        """
        self._meta = dict(meta)
        self.logger.debug(f"Set document metadata: {len(meta)} keys")
        return self

    def clear(self):
        """
        Clear all document content and reset the builder.
        
        Returns:
            Self for method chaining
        """
        self._title = None
        self._sections = []
        self._images = []
        self._meta = {}
        self.logger.info(f"Cleared document builder state (ID: {self.builder_id})")
        return self

    def build(self) -> DocumentData:
        """
        Build and return a DocumentData object with the current state.
        
        Returns:
            A new DocumentData object
            
        Raises:
            ValueError: If the document title is not set
        """
        if not self._title:
            self.logger.error("Cannot build document: title is required")
            raise ValueError("Document title is required")
            
        doc = DocumentData(
            title=self._title,
            sections=list(self._sections),
            images=list(self._images),
            meta=dict(self._meta),
        )
        
        self.logger.info(
            f"Built document '{self._title}'" + 
            f" with {len(self._sections)} sections," +
            f" {len(self._images)} images, and {len(self._meta)} meta keys"
        )
        return doc

    @classmethod
    def from_document(cls, doc: DocumentData) -> 'DocumentBuilder':
        """
        Create a new builder from an existing DocumentData object.
        
        Args:
            doc: The DocumentData object to copy
            
        Returns:
            A new DocumentBuilder with the copied content
        """
        builder = cls()
        builder.logger.info(f"Creating builder from existing document: '{doc.title}'")
        builder.set_title(doc.title)
        builder.add_sections(doc.sections)
        builder.add_images(doc.images)
        builder.set_meta(doc.meta)
        return builder
