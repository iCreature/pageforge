from abc import ABC, abstractmethod
from typing import Any, Dict, Union, Optional, List
import time
import uuid
import traceback

try:
    from ..models import DocumentData, Section
    from ..logging_config import get_logger
except ImportError:
    # For direct imports during testing
    from docuforge.models import DocumentData, Section
    from docuforge.logging_config import get_logger

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
        self.logger = get_logger(f"docuforge.engines.{self.name.lower()}")
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
            ValueError: If document structure is invalid
        """
        # Check for title
        if not hasattr(doc, "title") or not doc.title:
            self.logger.warning(f"Document has no title (ID: {render_id})")
        
        # Check for sections
        if not hasattr(doc, "sections") or not doc.sections:
            self.logger.warning(f"Document has no sections (ID: {render_id})")
        else:
            # Validate each section
            for i, section in enumerate(doc.sections):
                try:
                    # Check if section has required attributes
                    if isinstance(section, dict):
                        if "type" not in section:
                            self.logger.warning(f"Section {i} missing type field (ID: {render_id})")
                    elif hasattr(section, "type"):
                        stype = section.type
                        if stype not in ["text", "header", "footer", "table", "list"]:
                            self.logger.warning(f"Section {i} has unknown type: {stype} (ID: {render_id})")
                    else:
                        self.logger.warning(f"Section {i} has no type attribute (ID: {render_id})")
                except Exception as e:
                    self.logger.warning(f"Error validating section {i}: {str(e)} (ID: {render_id})")
        
        # Check for images
        if hasattr(doc, "images") and doc.images:
            for i, img in enumerate(doc.images):
                try:
                    # Check if image has data
                    if isinstance(img, dict):
                        if "data" not in img or not img.get("data"):
                            self.logger.warning(f"Image {i} has no data (ID: {render_id})")
                    elif not hasattr(img, "data") or not img.data:
                        self.logger.warning(f"Image {i} has no data attribute (ID: {render_id})")
                except Exception as e:
                    self.logger.warning(f"Error validating image {i}: {str(e)} (ID: {render_id})")

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

    def render(self, doc_or_dict: Union[Dict[str, Any], DocumentData]) -> bytes:
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
                if isinstance(e, (ValueError, TypeError)):
                    # Re-raise known errors
                    raise
                # Wrap unknown errors
                raise ValueError(f"PDF rendering failed: {str(e)}")
            
            # Validate output
            if not isinstance(out, bytes):
                self.logger.error(f"Engine returned {type(out).__name__}, expected bytes (ID: {render_id})")
                raise TypeError(f"Engine {self.name} must return bytes, got {type(out).__name__}")
            
            # Check if PDF output seems valid (basic check, relaxed for test engines)
            if len(out) < 10:  # Very minimal size check
                self.logger.warning(f"Generated content is suspiciously small ({len(out)} bytes) (ID: {render_id})")
                
            # Only do PDF signature check for production engines, not test engines
            if not self.__class__.__name__.startswith(('Dummy', 'Mock', 'Test')) and \
               not out.startswith(b'%PDF') and not b'%PDF' in out[:200]:
                self.logger.warning(f"Generated content does not have PDF signature (ID: {render_id})")
                # Log warning but don't fail - some test engines may return dummy content
                
            elapsed = time.time() - start_time
            self.logger.info(f"PDF rendering completed in {elapsed:.2f} seconds, size: {len(out)} bytes (ID: {render_id})")
            return out
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.exception(f"PDF rendering failed after {elapsed:.2f} seconds (ID: {render_id}): {str(e)}")
            raise

class EngineRegistry:
    """
    Registry for PDF rendering engines.
    
    This class provides a central registry for all available rendering engines,
    allowing them to be looked up by name. Engines must register themselves
    with this registry to be available for use.
    """
    _registry: Dict[str, Engine] = {}
    _logger = get_logger("docuforge.engines.registry")

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
