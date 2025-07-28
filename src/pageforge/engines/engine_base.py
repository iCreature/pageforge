import time
import traceback
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

try:
    from ..core.exceptions import (
        PageForgeError,
        ImageError,
        RenderingError,
        ResourceError,
        SectionError,
        ValidationError,
    )
    from ..core.models import DocumentData, Section
    from ..utils.logging_config import get_logger
except ImportError:
    # For direct imports during testing
    from pageforge.core.exceptions import (
        PageForgeError,
        ImageError,
        RenderingError,
        SectionError,
        ValidationError,
    )
    from pageforge.core.models import DocumentData
    from pageforge.utils.logging_config import get_logger

class Engine(ABC):
    """
    Abstract base class for all PDF engines.
    
    This class defines the interface that all rendering engines must implement.
    Engines are responsible for converting DocumentData objects into PDF bytes.
    
    Attributes:
        name: The name of the engine implementation
        logger: The logger instance for this engine
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the engine with a name and logger.
        
        Args:
            name: Optional name for this engine instance
        """
        self.name = name or self.__class__.__name__
        self.logger = get_logger(f"pageforge.engines.{self.name.lower()}")
        # Each instance gets a unique ID for traceability
        self.instance_id = str(uuid.uuid4())[:8]
        self.logger.debug(f"Initialized {self.name} engine instance {self.instance_id}")
    
    def _validate_document_structure(self, doc: DocumentData, render_id: str) -> None:
        """
        Validate document structure before rendering.
        
        Args:
            doc: The DocumentData object to validate
            render_id: The unique ID for this render operation
            
        Raises:
            ValidationError: If document structure is invalid
        """
        validation_warnings = []
        
        # Check for title
        if not hasattr(doc, "title") or not doc.title:
            warning = "Document has no title"
            validation_warnings.append(warning)
            self.logger.warning(f"{warning} (ID: {render_id})")
        
        # Check for sections
        if not hasattr(doc, "sections") or not doc.sections:
            warning = "Document has no sections"
            validation_warnings.append(warning)
            self.logger.warning(f"{warning} (ID: {render_id})")
        else:
            # Validate each section
            for i, section in enumerate(doc.sections):
                try:
                    # Check if section has required attributes
                    if isinstance(section, dict):
                        if "type" not in section:
                            warning = f"Section {i} missing type field"
                            validation_warnings.append(warning)
                            self.logger.warning(f"{warning} (ID: {render_id})")
                    elif hasattr(section, "type"):
                        stype = section.type
                        if stype not in ["paragraph", "header", "footer", "table", "list"]:
                            warning = f"Section {i} has unknown type: {stype}"
                            validation_warnings.append(warning)
                            self.logger.warning(f"{warning} (ID: {render_id})")
                    else:
                        warning = f"Section {i} has no type attribute"
                        validation_warnings.append(warning)
                        self.logger.warning(f"{warning} (ID: {render_id})")
                except Exception as e:
                    # Use SectionError for better error reporting
                    section_error = SectionError(
                        message="Error validating section",
                        section_index=i,
                        section_type=getattr(section, "type", "unknown") if hasattr(section, "type") else "unknown",
                        engine=self.__class__.__name__,
                        render_id=render_id,
                        details={"error_message": str(e)}
                    )
                    validation_warnings.append(str(section_error))
                    self.logger.warning(f"{section_error.message} {i}: {str(e)} (ID: {render_id})")
        
        # Check for images
        if hasattr(doc, "images") and doc.images:
            for i, img in enumerate(doc.images):
                try:
                    # Check if image has data
                    if isinstance(img, dict):
                        if "data" not in img or not img.get("data"):
                            warning = f"Image {i} has no data"
                            validation_warnings.append(warning)
                            self.logger.warning(f"{warning} (ID: {render_id})")
                    elif not hasattr(img, "data") or not img.data:
                        warning = f"Image {i} has no data attribute"
                        validation_warnings.append(warning)
                        self.logger.warning(f"{warning} (ID: {render_id})")
                except Exception as e:
                    # Use ImageError for better error reporting
                    img_error = ImageError(
                        message="Error validating image",
                        image_index=i,
                        image_name=getattr(img, "name", f"unnamed_image_{i}"),
                        format=getattr(img, "format", "unknown"),
                        details={
                            "render_id": render_id,
                            "error_message": str(e)
                        }
                    )
                    validation_warnings.append(str(img_error))
                    self.logger.warning(f"{img_error.message} {i}: {str(e)} (ID: {render_id})")
                    
        # If we have serious validation issues, we could raise a ValidationError here
        # For now, we just log warnings and continue, as this seems to be the existing behavior

    @abstractmethod
    def _render(self, doc: DocumentData) -> bytes:
        """
        Internal render method that must be implemented by subclasses.
        
        Args:
            doc: The DocumentData object to render
            
        Returns:
            PDF document as bytes
            
        Raises:
            NotImplementedError: If not implemented by subclass
            ValueError: If document structure is invalid
            TypeError: If expected types are incorrect
        """
        raise NotImplementedError(f"Engine {self.__class__.__name__} must implement _render method")

    def render(self, doc_or_dict: Union[dict[str, Any], DocumentData]) -> bytes:
        """
        Public render method that converts input data to DocumentData and renders it to PDF.
        
        Args:
            doc_or_dict: Either a DocumentData object or a dictionary with document fields
            
        Returns:
            PDF document as bytes
            
        Raises:
            TypeError: If input is not a dict or DocumentData or if output is not bytes
            ValueError: If document structure is invalid
        """
        # Generate a unique render ID for this operation
        render_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        self.logger.info(f"Starting PDF rendering with {self.name} engine (ID: {render_id})")
        
        try:
            # Convert input to DocumentData if necessary
            if isinstance(doc_or_dict, dict):
                self.logger.debug(f"Converting dictionary to DocumentData (ID: {render_id})")
                try:
                    doc = DocumentData(**{k: v for k, v in doc_or_dict.items() 
                                        if k in DocumentData.__dataclass_fields__})
                except Exception as e:
                    self.logger.error(f"Failed to convert dictionary to DocumentData (ID: {render_id}): {str(e)}")
                    raise ValueError(f"Invalid document data structure: {str(e)}")
            elif isinstance(doc_or_dict, DocumentData):
                self.logger.debug(f"Using provided DocumentData object (ID: {render_id})")
                doc = doc_or_dict
            else:
                self.logger.error(f"Invalid input type: {type(doc_or_dict).__name__} (ID: {render_id})")
                raise TypeError(f"Input must be DocumentData or dict, got {type(doc_or_dict).__name__}")
            
            # Validate document structure
            self._validate_document_structure(doc, render_id)
                
            # Log document structure information
            sections_count = len(getattr(doc, "sections", []))
            images_count = len(getattr(doc, "images", []))
            title = getattr(doc, "title", "Untitled")
            self.logger.info(f"Rendering document '{title}' with {sections_count} sections and {images_count} images (ID: {render_id})")
            
            # Call internal render method
            try:
                out = self._render(doc)
            except Exception as e:
                stack_trace = traceback.format_exc()
                self.logger.error(f"Engine rendering error (ID: {render_id}): {str(e)}\n{stack_trace}")
                
                # Handle different exception types appropriately
                if isinstance(e, PageForgeError):
                    # Re-raise our custom exceptions as is
                    raise
                elif isinstance(e, (ValueError, TypeError)):
                    # Wrap standard exceptions with our custom exceptions
                    if "image" in str(e).lower():
                        raise ImageError(
                            message="Image processing error",
                            details={
                                "render_id": render_id,
                                "error_message": str(e),
                                "error_type": e.__class__.__name__
                            }
                        ) from e
                    elif "section" in str(e).lower():
                        raise SectionError(
                            message="Section processing error",
                            engine=self.__class__.__name__,
                            render_id=render_id,
                            details={
                                "error_message": str(e),
                                "error_type": e.__class__.__name__
                            }
                        ) from e
                    else:
                        # Generic validation error
                        raise ValidationError(
                            message="Document validation error",
                            details={
                                "render_id": render_id,
                                "error_message": str(e),
                                "error_type": e.__class__.__name__
                            }
                        ) from e
                else:
                    # Wrap unknown errors with RenderingError
                    raise RenderingError(
                        message="PDF rendering failed",
                        engine=self.__class__.__name__,
                        render_id=render_id,
                        cause=e,
                        details={
                            "error_message": str(e),
                            "error_type": e.__class__.__name__
                        }
                    ) from e
            
            # Validate output
            if not isinstance(out, bytes):
                self.logger.error(f"Engine returned {type(out).__name__}, expected bytes (ID: {render_id})")
                raise ValidationError(
                    message="Engine output validation failed",
                    field="output",
                    value=type(out).__name__,
                    expected="bytes",
                    details={
                        "render_id": render_id,
                        "engine": self.name
                    }
                )
            
            # Check if PDF output seems valid (basic check, relaxed for test engines)
            if len(out) < 10:  # Very minimal size check
                self.logger.warning(f"Generated content is suspiciously small ({len(out)} bytes) (ID: {render_id})")
                
            # Only do PDF signature check for production engines, not test engines
            if not self.__class__.__name__.startswith(('Dummy', 'Mock', 'Test')) and \
               not out.startswith(b'%PDF') and b'%PDF' not in out[:200]:
                self.logger.warning(f"Generated content does not have PDF signature (ID: {render_id})")
                # Log warning but don't fail - some test engines may return dummy content
                
            elapsed = time.time() - start_time
            self.logger.info(f"PDF rendering completed in {elapsed:.2f} seconds, size: {len(out)} bytes (ID: {render_id})")
            return out
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.exception(f"PDF rendering failed after {elapsed:.2f} seconds (ID: {render_id}): {str(e)}")
            
            # If it's not already a PageForgeError, wrap it
            if not isinstance(e, PageForgeError):
                raise RenderingError(
                    message="Unexpected error during PDF generation",
                    engine=self.__class__.__name__,
                    render_id=render_id,
                    cause=e,
                    details={
                        "elapsed_time": round(elapsed, 3),
                        "error_message": str(e),
                        "error_type": e.__class__.__name__
                    }
                ) from e
            raise

class EngineRegistry:
    """
    Registry for PDF rendering engines.
    
    This class provides a central registry for all available rendering engines,
    allowing them to be looked up by name. Engines must register themselves
    with this registry to be available for use.
    """
    _registry: dict[str, Engine] = {}
    _logger = get_logger("pageforge.engines.registry")

    @classmethod
    def register(cls, name: str, engine: Engine) -> None:
        """
        Register a new engine with the registry.
        
        Args:
            name: The name to register the engine under
            engine: The engine instance to register
        """
        cls._logger.info(f"Registering engine: {name}")
        cls._registry[name] = engine

    @classmethod
    def get(cls, name: str) -> Engine:
        """
        Get an engine by name.
        
        Args:
            name: The name of the engine to retrieve
            
        Returns:
            The registered engine instance
            
        Raises:
            KeyError: If no engine is registered with the given name
        """
        if name not in cls._registry:
            cls._logger.error(f"Engine '{name}' not found in registry")
            available = ", ".join(cls._registry.keys()) or "none"
            cls._logger.info(f"Available engines: {available}")
            raise KeyError(f"Engine '{name}' not registered. Available: {available}")
            
        cls._logger.debug(f"Retrieved engine: {name}")
        return cls._registry[name]
