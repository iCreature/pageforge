"""
Font management system for PageForge.

This module provides a unified interface for registering, managing, and selecting fonts
for various document rendering engines, with support for:
- Custom font registration
- International text support (CJK, Cyrillic, etc.)
- Right-to-left (RTL) text handling
- Font fallback chains
"""

import os

# ReportLab imports
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Import our custom exceptions
try:
    from ..core.exceptions import FontError, ResourceError
    from ..utils.logging_config import get_logger
except ImportError:
    # For direct imports during testing
    from pageforge.utils.logging_config import get_logger

# Logger setup
logger = get_logger(__name__)

# Standard system font directories
SYSTEM_FONT_DIRS = [
    # Linux
    '/usr/share/fonts',
    '/usr/local/share/fonts',
    # macOS
    '/System/Library/Fonts',
    '/Library/Fonts',
    # Windows
    'C:/Windows/Fonts',
    # User fonts
    os.path.expanduser('~/.fonts'),
    os.path.expanduser('~/Library/Fonts'),
]

# Font detection for different scripts
SCRIPT_TO_FONT_MAP = {
    # Latin scripts
    'latin': ['DejaVuSans', 'Arial', 'Helvetica', 'Times-Roman'],
    # CJK scripts
    'chinese': ['STSong-Light', 'SimSun', 'Source Han Sans CN'],
    'japanese': ['HeiseiMin-W3', 'MS-Mincho', 'Source Han Sans JP'],
    'korean': ['HYGothic-Medium', 'Malgun Gothic', 'Source Han Sans KR'],
    # RTL scripts
    'arabic': ['Arial Unicode MS', 'DejaVuSans', 'Noto Sans Arabic'],
    'hebrew': ['Arial Unicode MS', 'DejaVuSans', 'Noto Sans Hebrew'],
    # Other scripts
    'cyrillic': ['DejaVuSans', 'Arial Unicode MS', 'Noto Sans'],
    'devanagari': ['Noto Sans Devanagari', 'Mangal', 'Arial Unicode MS'],
    'thai': ['Noto Sans Thai', 'Tahoma', 'Arial Unicode MS'],
}

# RTL language codes
RTL_LANGUAGES = {'ar', 'he', 'fa', 'ur', 'ps', 'sd', 'yi', 'dv'}

# Font file extensions
FONT_EXTENSIONS = {'.ttf', '.otf', '.ttc', '.pfb', '.woff', '.woff2'}

class FontManager:
    """
    Manages font registration, fallbacks, and script/language detection for PageForge.
    
    The FontManager:
    1. Discovers fonts from system locations and custom directories
    2. Registers fonts with PDF rendering engines
    3. Provides font selection for different scripts and languages
    4. Handles RTL text detection and processing
    5. Maintains fallback chains to ensure text always renders
    """
    
    def __init__(self, 
                 custom_font_dirs: list[str] = None,
                 default_font: str = 'Helvetica',
                 enable_rtl: bool = True):
        """
        Initialize the font manager.
        
        Args:
            custom_font_dirs: Optional list of additional directories to search for fonts
            default_font: Default font to use when no other font is specified
            enable_rtl: Whether to enable RTL text detection and handling
        """
        self.custom_font_dirs = custom_font_dirs or []
        self.default_font = default_font
        self.enable_rtl = enable_rtl
        
        # Track registered fonts
        self.registered_fonts: set[str] = set()
        self.font_paths: dict[str, str] = {}
        self.cid_fonts: set[str] = set()
        self.script_fonts: dict[str, list[str]] = {}
        
        # Initialize with engine-specific default fonts
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize with engine defaults."""
        # Always consider the PDF base 14 fonts as registered
        self.registered_fonts.update([
            'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique', 'Helvetica-BoldOblique',
            'Times-Roman', 'Times-Bold', 'Times-Italic', 'Times-BoldItalic',
            'Courier', 'Courier-Bold', 'Courier-Oblique', 'Courier-BoldOblique',
            'Symbol', 'ZapfDingbats'
        ])
        
        # Copy initial script-to-font mappings
        self.script_fonts = SCRIPT_TO_FONT_MAP.copy()
    
    def discover_fonts(self) -> dict[str, str]:
        """
        Discover fonts from system and custom directories.
        
        Returns:
            Dictionary mapping font family names to file paths
        """
        discovered_fonts: dict[str, str] = {}
        
        # Combine system and custom directories
        search_dirs = SYSTEM_FONT_DIRS + self.custom_font_dirs
        
        for base_dir in search_dirs:
            if not os.path.exists(base_dir):
                continue
                
            try:
                # Walk through the directory tree
                for root, _, files in os.walk(base_dir):
                    for file in files:
                        lower_file = file.lower()
                        # Check if this is a font file by extension
                        if any(lower_file.endswith(ext) for ext in FONT_EXTENSIONS):
                            font_path = os.path.join(root, file)
                            # Extract font family name from filename (simplified)
                            font_name = os.path.splitext(file)[0]
                            discovered_fonts[font_name] = font_path
                            
            except (PermissionError, OSError) as e:
                logger.warning(f"Error scanning font directory {base_dir}: {str(e)}")
        
        return discovered_fonts
    
    def register_font(self, font_name: str, font_path: str = None) -> bool:
        """
        Register a font with the rendering engine.
        
        Args:
            font_name: Name of the font to register
            font_path: Optional path to the font file
            
        Returns:
            True if registration was successful, False otherwise
        """
        # Skip if already registered
        if font_name in self.registered_fonts:
            return True
            
        if not REPORTLAB_AVAILABLE:
            logger.warning(f"ReportLab not available, can't register font: {font_name}")
            return False
            
        try:
            # Try as CID font first (for international support)
            if font_path is None:
                try:
                    pdfmetrics.registerFont(UnicodeCIDFont(font_name))
                    self.registered_fonts.add(font_name)
                    self.cid_fonts.add(font_name)
                    logger.debug(f"Registered CID font: {font_name}")
                    return True
                except Exception as e:
                    logger.debug(f"Not a CID font ({font_name}): {str(e)}")
                    # Continue to try as TTF
            
            # Register as TTF if path provided
            if font_path and os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                self.registered_fonts.add(font_name)
                self.font_paths[font_name] = font_path
                logger.debug(f"Registered TTF font: {font_name} from {font_path}")
                
                # Try to register bold, italic variants based on naming patterns
                base_dir = os.path.dirname(font_path)
                base_name = os.path.splitext(os.path.basename(font_path))[0]
                
                # Common suffix patterns
                variant_patterns = {
                    'Bold': ['-Bold', 'Bold', '_Bold', 'B'],
                    'Italic': ['-Italic', 'Italic', '_Italic', 'I', 'Oblique'],
                    'BoldItalic': ['-BoldItalic', 'BoldItalic', 'BoldOblique']
                }
                
                # Try to register variants
                for variant, suffixes in variant_patterns.items():
                    for suffix in suffixes:
                        for ext in FONT_EXTENSIONS:
                            variant_filename = f"{base_name}{suffix}{ext}"
                            variant_path = os.path.join(base_dir, variant_filename)
                            variant_name = f"{font_name}-{variant}"
                            
                            if os.path.exists(variant_path) and variant_name not in self.registered_fonts:
                                try:
                                    pdfmetrics.registerFont(TTFont(variant_name, variant_path))
                                    self.registered_fonts.add(variant_name)
                                    self.font_paths[variant_name] = variant_path
                                    logger.debug(f"Registered variant font: {variant_name}")
                                except Exception as e:
                                    logger.debug(f"Failed to register variant {variant_name}: {str(e)}")
                
                # Try to register font family if we have variants
                try:
                    family = {}
                    if font_name in self.registered_fonts:
                        family['normal'] = font_name
                    if f"{font_name}-Bold" in self.registered_fonts:
                        family['bold'] = f"{font_name}-Bold"
                    if f"{font_name}-Italic" in self.registered_fonts:
                        family['italic'] = f"{font_name}-Italic"
                    if f"{font_name}-BoldItalic" in self.registered_fonts:
                        family['boldItalic'] = f"{font_name}-BoldItalic"
                        
                    if len(family) > 1:  # At least normal and one variant
                        pdfmetrics.registerFontFamily(font_name, **family)
                        logger.debug(f"Registered font family: {font_name}")
                except Exception as e:
                    logger.debug(f"Failed to register font family {font_name}: {str(e)}")
                
                return True
                
            logger.warning(f"Font not found or invalid path: {font_name}, {font_path}")
            return False
            
        except Exception as e:
            logger.warning(f"Error registering font {font_name}: {str(e)}")
            return False
    
    def register_system_fonts(self, priority_fonts: list[str] = None) -> int:
        """
        Register available system fonts.
        
        Args:
            priority_fonts: List of font names to prioritize registration
            
        Returns:
            Number of successfully registered fonts
        """
        count = 0
        discovered = self.discover_fonts()
        
        # Register priority fonts first
        if priority_fonts:
            for font in priority_fonts:
                for name, path in discovered.items():
                    if font.lower() in name.lower():
                        if self.register_font(name, path):
                            count += 1
        
        # Register common CID fonts for international support
        for script, fonts in SCRIPT_TO_FONT_MAP.items():
            for font in fonts:
                if font not in self.registered_fonts:
                    try:
                        if self.register_font(font):
                            count += 1
                    except Exception as e:
                        logger.debug(f"Failed to register {script} font {font}: {str(e)}")
        
        return count
    
    def is_rtl_text(self, text: str) -> bool:
        """
        Check if text contains RTL characters.
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains RTL characters
        """
        if not self.enable_rtl:
            return False
            
        # Check for Arabic, Hebrew and other RTL unicode ranges
        rtl_ranges = [
            (0x0590, 0x05FF),  # Hebrew
            (0x0600, 0x06FF),  # Arabic
            (0x0750, 0x077F),  # Arabic Supplement
            (0x08A0, 0x08FF),  # Arabic Extended-A
            (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
            (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
            (0x10800, 0x10FFF),  # Other RTL scripts
        ]
        
        for char in text:
            code = ord(char)
            for start, end in rtl_ranges:
                if start <= code <= end:
                    return True
                    
        return False
    
    def get_font_for_text(self, text: str, default: str = None) -> str:
        """
        Select the best font for rendering the given text.
        
        Args:
            text: Text to render
            default: Default font name if no suitable font is found
            
        Returns:
            Name of the best font to use
        """
        if not text:
            return default or self.default_font
            
        # Check for RTL text first
        if self.is_rtl_text(text):
            # Try Arabic or Hebrew fonts
            for font in self.script_fonts.get('arabic', []) + self.script_fonts.get('hebrew', []):
                if font in self.registered_fonts:
                    return font
        
        # Check for CJK characters
        cjk_ranges = [
            (0x4E00, 0x9FFF),   # CJK Unified Ideographs
            (0x3040, 0x309F),   # Hiragana
            (0x30A0, 0x30FF),   # Katakana
            (0xAC00, 0xD7AF)    # Hangul Syllables
        ]
        
        for char in text:
            code = ord(char)
            # Check if character is CJK
            for start, end in cjk_ranges:
                if start <= code <= end:
                    # Try Japanese, Chinese, Korean fonts
                    for script in ['japanese', 'chinese', 'korean']:
                        for font in self.script_fonts.get(script, []):
                            if font in self.registered_fonts:
                                return font
        
        # Check for Cyrillic
        cyrillic_range = (0x0400, 0x04FF)
        for char in text:
            code = ord(char)
            if cyrillic_range[0] <= code <= cyrillic_range[1]:
                for font in self.script_fonts.get('cyrillic', []):
                    if font in self.registered_fonts:
                        return font
        
        # Default to Latin fonts
        for font in self.script_fonts.get('latin', []):
            if font in self.registered_fonts:
                return font
                
        # Fall back to specified default or class default
        return default or self.default_font
    
    def process_rtl_text(self, text: str) -> str:
        """
        Process RTL text for proper rendering.
        
        Args:
            text: Text to process
            
        Returns:
            Processed text ready for rendering
        """
        if not self.enable_rtl or not self.is_rtl_text(text):
            return text
            
        try:
            # Try to use python-bidi for proper bidirectional text handling
            try:
                from bidi.algorithm import get_display
                return get_display(text)
            except ImportError:
                logger.debug("python-bidi not available, falling back to basic RTL handling")
                
            # Very basic RTL handling (just mark it as RTL)
            # This assumes the rendering engine will handle it
            # In real-world usage, python-bidi should be used
            if text and self.is_rtl_text(text):
                # Unicode RTL mark + original text
                return "\u200F" + text
                
        except Exception as e:
            logger.warning(f"Error processing RTL text: {str(e)}")
            
        return text
