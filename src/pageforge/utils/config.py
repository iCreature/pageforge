"""
PageForge Configuration Module

This module provides configuration management for the PageForge library.
It handles loading configuration from environment variables, configuration files,
and provides sensible defaults for all parameters.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

# Default configuration values
DEFAULT_CONFIG = {
    # Page settings
    "page": {
        "width": 612.0,  # Letter size width (in points)
        "height": 792.0,  # Letter size height (in points)
        "margin": 72.0,   # 1 inch margin (in points)
    },
    # Text settings
    "text": {
        "default_font": "Helvetica",
        "default_size": 12,
        "header_size": 16,
        "line_height": 18,
        "max_width": 468.0,  # Page width - 2*margin = 612 - 2*72 = 468
    },
    # Image settings
    "image": {
        "max_count": 10,
        "default_width": 120.0,
        "default_height": 80.0,
        "formats": ["png", "jpg", "jpeg"],
    },
    # Font settings
    "fonts": {
        "builtin": ["Helvetica", "Courier", "Times-Roman"],
        "cid": {
            "japanese": "HeiseiMin-W3",
            "korean": "HYSMyeongJoStd-Medium",
            "chinese": "STSong-Light"
        }
    },
    # Security settings
    "security": {
        "max_content_size_mb": 5,  # Maximum size of document content in MB
        "allowed_image_formats": ["png", "jpg", "jpeg", "gif"],
        "disable_external_resources": True,  # Don't allow external resources in HTML rendering
    },
    # Rendering settings
    "rendering": {
        "default_engine": "reportlab",
        "timeout_seconds": 30,  # Maximum time to render a document
        "max_pages": 100,  # Maximum number of pages to render
    },
    # Logging settings (minimal as most are in logging_config.py)
    "logging": {
        "log_level": "INFO",
    }
}

# Environment variable prefix for PageForge configuration
ENV_PREFIX = "PAGEFORGE_"


@dataclass
class PageConfig:
    """Configuration for page dimensions and layout"""
    width: float = 612.0
    height: float = 792.0
    margin: float = 72.0


@dataclass
class TextConfig:
    """Configuration for text rendering"""
    default_font: str = "Helvetica"
    default_size: int = 12
    header_size: int = 16
    line_height: int = 18
    max_width: float = 468.0


@dataclass
class ImageConfig:
    """Configuration for image handling"""
    max_count: int = 10
    default_width: float = 120.0
    default_height: float = 80.0
    formats: list[str] = field(default_factory=lambda: ["png", "jpg", "jpeg"])


@dataclass
class FontsConfig:
    """Configuration for fonts"""
    builtin: list[str] = field(default_factory=lambda: ["Helvetica", "Courier", "Times-Roman"])
    cid: dict[str, str] = field(default_factory=lambda: {
        "japanese": "HeiseiMin-W3",
        "korean": "HYSMyeongJoStd-Medium", 
        "chinese": "STSong-Light"
    })


@dataclass
class SecurityConfig:
    """Configuration for security settings"""
    max_content_size_mb: int = 5
    allowed_image_formats: list[str] = field(default_factory=lambda: ["png", "jpg", "jpeg", "gif"])
    disable_external_resources: bool = True


@dataclass
class RenderingConfig:
    """Configuration for rendering settings"""
    default_engine: str = "reportlab"
    timeout_seconds: int = 30
    max_pages: int = 100


@dataclass
class LoggingConfig:
    """Configuration for logging settings"""
    log_level: str = "INFO"


@dataclass
class PageForgeConfig:
    """Main configuration class for PageForge"""
    page: PageConfig = field(default_factory=PageConfig)
    text: TextConfig = field(default_factory=TextConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    fonts: FontsConfig = field(default_factory=FontsConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    rendering: RenderingConfig = field(default_factory=RenderingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)


class ConfigManager:
    """
    Configuration manager for PageForge.
    
    This class handles loading configuration from different sources
    with the following precedence:
    1. Environment variables
    2. Configuration file
    3. Default values
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = PageForgeConfig()
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration manager if not already initialized"""
        if not self._initialized:
            self._load_defaults()
            self._initialized = True
    
    def _load_defaults(self):
        """Load default configuration values"""
        # Already initialized via dataclass defaults
        pass
    
    def _env_var_name(self, section: str, key: str) -> str:
        """Convert section and key to environment variable name"""
        return f"{ENV_PREFIX}{section.upper()}_{key.upper()}"
    
    def _parse_env_value(self, value: str, target_type: type):
        """Parse environment variable value to target type"""
        if target_type == bool:
            return value.lower() in ("yes", "true", "t", "1")
        if target_type == int:
            return int(value)
        if target_type == float:
            return float(value)
        if target_type == list or target_type == list:
            # Parse comma-separated list
            return [item.strip() for item in value.split(",")]
        if target_type == dict or target_type == dict:
            # Parse JSON string
            return json.loads(value)
        # Default to string
        return value
    
    def load_from_env(self):
        """Load configuration from environment variables"""
        config_dict = self.to_dict()
        
        for section_name, section in config_dict.items():
            if isinstance(section, dict):
                for key, value in section.items():
                    env_var_name = self._env_var_name(section_name, key)
                    if env_var_name in os.environ:
                        try:
                            parsed_value = self._parse_env_value(
                                os.environ[env_var_name], 
                                type(value)
                            )
                            # Update config
                            getattr(self._config, section_name).__setattr__(key, parsed_value)
                        except Exception as e:
                            print(f"Error parsing environment variable {env_var_name}: {str(e)}")
    
    def load_from_file(self, filepath: Union[str, Path]):
        """
        Load configuration from a JSON file
        
        Args:
            filepath: Path to the configuration file
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        try:
            with open(filepath) as f:
                file_config = json.load(f)
            
            # Update config with values from file
            for section_name, section in file_config.items():
                if hasattr(self._config, section_name) and isinstance(section, dict):
                    section_config = getattr(self._config, section_name)
                    for key, value in section.items():
                        if hasattr(section_config, key):
                            setattr(section_config, key, value)
        except Exception as e:
            raise ValueError(f"Error loading configuration file: {str(e)}")
    
    def get_config(self) -> PageForgeConfig:
        """Get the current configuration"""
        return self._config
    
    def to_dict(self) -> dict[str, Any]:
        """Convert current configuration to dictionary"""
        return self._config.to_dict()


# Global configuration instance
_config_manager = None


def get_config() -> PageForgeConfig:
    """
    Get the global configuration instance
    
    Returns:
        PageForgeConfig: The current configuration
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        # Load from environment by default
        _config_manager.load_from_env()
        
        # Load from file if specified in environment
        config_file_path = os.environ.get(f"{ENV_PREFIX}CONFIG_FILE")
        if config_file_path:
            try:
                _config_manager.load_from_file(config_file_path)
            except Exception as e:
                print(f"Warning: Failed to load config file: {str(e)}")
    
    return _config_manager.get_config()


def init_config(config_file: Optional[Union[str, Path]] = None) -> PageForgeConfig:
    """
    Initialize configuration with optional config file
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        PageForgeConfig: The initialized configuration
    """
    global _config_manager
    _config_manager = ConfigManager()
    
    # Load from environment
    _config_manager.load_from_env()
    
    # Load from file if provided
    if config_file:
        _config_manager.load_from_file(config_file)
    
    return _config_manager.get_config()
