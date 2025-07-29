"""
PageForge Exception Classes

This module defines the exception hierarchy used throughout PageForge.
These exceptions provide standardized error handling and reporting.
"""

from typing import Any, Optional


class PageForgeError(Exception):
    """Base exception class for all PageForge errors."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """
        Initialize a PageForge error with a message and optional details.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error information
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PageForgeError):
    """Raised when input validation fails."""
    
    def __init__(self, 
                 message: str, 
                 field: Optional[str] = None,
                 value: Optional[Any] = None,
                 expected: Optional[str] = None,
                 details: Optional[dict[str, Any]] = None):
        """
        Initialize a validation error with detailed information.
        
        Args:
            message: Human-readable error message
            field: Name of the field that failed validation
            value: The invalid value that was provided
            expected: Description of what was expected
            details: Optional dictionary with additional error information
        """
        self.field = field
        self.invalid_value = value
        self.expected = expected
        
        # Add specific fields to details
        complete_details = details or {}
        if field:
            complete_details['field'] = field
        if value is not None:
            try:
                # Try to represent the value as a string if possible
                complete_details['value'] = str(value)
            except:
                complete_details['value'] = f"<unprintable value of type {type(value).__name__}>"
        if expected:
            complete_details['expected'] = expected
            
        super().__init__(message, complete_details)


class RenderingError(PageForgeError):
    """Raised when document rendering fails."""
    
    def __init__(self, 
                 message: str, 
                 engine: Optional[str] = None,
                 render_id: Optional[str] = None,
                 section_index: Optional[int] = None,
                 cause: Optional[Exception] = None,
                 details: Optional[dict[str, Any]] = None):
        """
        Initialize a rendering error with detailed information.
        
        Args:
            message: Human-readable error message
            engine: Name of the rendering engine that encountered the error
            render_id: ID of the rendering operation for traceability
            section_index: Index of the section being rendered when error occurred
            cause: The underlying exception that caused this error
            details: Optional dictionary with additional error information
        """
        self.engine = engine
        self.render_id = render_id
        self.section_index = section_index
        self.cause = cause
        
        # Add specific fields to details
        complete_details = details or {}
        if engine:
            complete_details['engine'] = engine
        if render_id:
            complete_details['render_id'] = render_id
        if section_index is not None:
            complete_details['section_index'] = section_index
        if cause:
            complete_details['cause'] = str(cause)
            
        super().__init__(message, complete_details)


class ResourceError(PageForgeError):
    """Raised when there is an issue with resource handling (fonts, images, etc)."""
    
    def __init__(self, 
                 message: str, 
                 resource_type: Optional[str] = None,
                 resource_name: Optional[str] = None,
                 details: Optional[dict[str, Any]] = None):
        """
        Initialize a resource error with detailed information.
        
        Args:
            message: Human-readable error message
            resource_type: Type of resource (font, image, etc.)
            resource_name: Name or identifier of the resource
            details: Optional dictionary with additional error information
        """
        self.resource_type = resource_type
        self.resource_name = resource_name
        
        # Add specific fields to details
        complete_details = details or {}
        if resource_type:
            complete_details['resource_type'] = resource_type
        if resource_name:
            complete_details['resource_name'] = resource_name
            
        super().__init__(message, complete_details)


class ConfigurationError(PageForgeError):
    """Raised when there is an issue with configuration."""
    
    def __init__(self, 
                 message: str, 
                 config_key: Optional[str] = None,
                 details: Optional[dict[str, Any]] = None):
        """
        Initialize a configuration error with detailed information.
        
        Args:
            message: Human-readable error message
            config_key: The configuration key that has an issue
            details: Optional dictionary with additional error information
        """
        self.config_key = config_key
        
        # Add specific fields to details
        complete_details = details or {}
        if config_key:
            complete_details['config_key'] = config_key
            
        super().__init__(message, complete_details)


class ImageError(ResourceError):
    """Specialized error for image-related issues."""
    
    def __init__(self, 
                 message: str, 
                 image_index: Optional[int] = None,
                 image_name: Optional[str] = None,
                 format: Optional[str] = None,
                 details: Optional[dict[str, Any]] = None):
        """
        Initialize an image error with detailed information.
        
        Args:
            message: Human-readable error message
            image_index: Index of the image in the document
            image_name: Name of the image
            format: Format of the image
            details: Optional dictionary with additional error information
        """
        self.image_index = image_index
        self.format = format
        
        # Add specific fields to details
        complete_details = details or {}
        if image_index is not None:
            complete_details['image_index'] = image_index
        if format:
            complete_details['format'] = format
            
        super().__init__(
            message, 
            resource_type="image", 
            resource_name=image_name,
            details=complete_details
        )


class FontError(ResourceError):
    """Specialized error for font-related issues."""
    
    def __init__(self, 
                 message: str, 
                 font_name: Optional[str] = None,
                 script: Optional[str] = None,
                 details: Optional[dict[str, Any]] = None):
        """
        Initialize a font error with detailed information.
        
        Args:
            message: Human-readable error message
            font_name: Name of the font
            script: Script the font was intended for (e.g., 'japanese')
            details: Optional dictionary with additional error information
        """
        self.script = script
        
        # Add specific fields to details
        complete_details = details or {}
        if script:
            complete_details['script'] = script
            
        super().__init__(
            message, 
            resource_type="font", 
            resource_name=font_name,
            details=complete_details
        )


class SectionError(RenderingError):
    """Specialized error for section processing issues."""
    
    def __init__(self, 
                 message: str, 
                 section_type: Optional[str] = None,
                 section_index: Optional[int] = None,
                 engine: Optional[str] = None,
                 render_id: Optional[str] = None,
                 details: Optional[dict[str, Any]] = None):
        """
        Initialize a section error with detailed information.
        
        Args:
            message: Human-readable error message
            section_type: Type of the section (paragraph, table, etc.)
            section_index: Index of the section in the document
            engine: Name of the rendering engine
            render_id: ID of the rendering operation
            details: Optional dictionary with additional error information
        """
        self.section_type = section_type
        
        # Add specific fields to details
        complete_details = details or {}
        if section_type:
            complete_details['section_type'] = section_type
            
        super().__init__(
            message,
            engine=engine,
            render_id=render_id,
            section_index=section_index,
            details=complete_details
        )
