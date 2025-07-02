from abc import ABC, abstractmethod
from typing import Any, Dict, Union, Optional
import time

try:
    from ..models import DocumentData
    from ..logging_config import get_logger
except ImportError:
    # For direct imports during testing
    from docuforge.models import DocumentData
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
        """
        raise NotImplementedError("Engines must implement _render method")

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
        start_time = time.time()
        self.logger.info(f"Starting PDF rendering with {self.name} engine")
        
        try:
            # Convert input to DocumentData if necessary
            if isinstance(doc_or_dict, dict):
                self.logger.debug("Converting dictionary to DocumentData")
                doc = DocumentData(**{k: v for k, v in doc_or_dict.items() 
                                     if k in DocumentData.__dataclass_fields__})
            elif isinstance(doc_or_dict, DocumentData):
                self.logger.debug("Using provided DocumentData object")
                doc = doc_or_dict
            else:
                self.logger.error(f"Invalid input type: {type(doc_or_dict).__name__}")
                raise TypeError("Input must be DocumentData or dict")
                
            # Log document structure information
            sections_count = len(getattr(doc, "sections", []))
            images_count = len(getattr(doc, "images", []))
            self.logger.info(f"Rendering document with {sections_count} sections and {images_count} images")
            
            # Call internal render method
            out = self._render(doc)
            
            # Validate output
            if not isinstance(out, bytes):
                self.logger.error(f"Engine returned {type(out).__name__}, expected bytes")
                raise TypeError(f"Engine {self.name} must return bytes, got {type(out).__name__}")
                
            elapsed = time.time() - start_time
            self.logger.info(f"PDF rendering completed in {elapsed:.2f} seconds, size: {len(out)} bytes")
            return out
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.exception(f"PDF rendering failed after {elapsed:.2f} seconds: {str(e)}")
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
