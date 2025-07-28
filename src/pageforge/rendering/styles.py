"""
Styles module for PageForge.

This module defines styling options for document elements including tables, paragraphs,
headers, and other document components. It provides a consistent interface for styling
across different rendering engines.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# Color definitions (RGB tuples)
class Color:
    """Color constants for styling elements."""
    BLACK = (0, 0, 0)
    WHITE = (1, 1, 1)
    RED = (1, 0, 0)
    GREEN = (0, 1, 0)
    BLUE = (0, 0, 1)
    GRAY = (0.5, 0.5, 0.5)
    LIGHT_GRAY = (0.9, 0.9, 0.9)
    DARK_GRAY = (0.25, 0.25, 0.25)
    
    # Common business colors
    NAVY = (0, 0, 0.5)
    TEAL = (0, 0.5, 0.5)
    MAROON = (0.5, 0, 0)
    PURPLE = (0.5, 0, 0.5)
    OLIVE = (0.5, 0.5, 0)

class HorizontalAlignment(str, Enum):
    """Horizontal alignment options for text and table content."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"

class VerticalAlignment(str, Enum):
    """Vertical alignment options for table cells."""
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"

class BorderStyle(str, Enum):
    """Border style options for tables and other elements."""
    NONE = "none"
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    DOUBLE = "double"

@dataclass
class Border:
    """
    Defines border properties for tables and other elements.
    """
    width: float = 1.0
    color: tuple[float, float, float] = Color.BLACK
    style: BorderStyle = BorderStyle.SOLID
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "width": self.width,
            "color": self.color,
            "style": self.style.value
        }

@dataclass
class TableCellStyle:
    """
    Defines styling for individual table cells.
    """
    background_color: Optional[tuple[float, float, float]] = None
    text_color: tuple[float, float, float] = Color.BLACK
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    bold: bool = False
    italic: bool = False
    horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT
    vertical_alignment: VerticalAlignment = VerticalAlignment.MIDDLE
    padding: tuple[float, float, float, float] = (2, 2, 2, 2)  # left, right, top, bottom
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "background_color": self.background_color,
            "text_color": self.text_color,
            "font_name": self.font_name,
            "font_size": self.font_size,
            "bold": self.bold,
            "italic": self.italic,
            "horizontal_alignment": self.horizontal_alignment.value,
            "vertical_alignment": self.vertical_alignment.value,
            "padding": self.padding
        }

@dataclass
class TableStyle:
    """
    Defines styling for an entire table.
    """
    # Border properties
    outer_border: Border = field(default_factory=Border)
    inner_horizontal_border: Border = field(default_factory=Border)
    inner_vertical_border: Border = field(default_factory=Border)
    
    # Header row styling
    header_style: TableCellStyle = field(default_factory=lambda: TableCellStyle(
        background_color=Color.LIGHT_GRAY,
        bold=True
    ))
    
    # Row styling (alternating rows)
    odd_row_style: Optional[TableCellStyle] = field(default_factory=TableCellStyle)
    even_row_style: Optional[TableCellStyle] = field(default_factory=lambda: TableCellStyle(
        background_color=(0.95, 0.95, 0.95)
    ))
    
    # Column-specific styling
    column_styles: dict[int, TableCellStyle] = field(default_factory=dict)
    
    # Cell-specific styling (row, col) -> style
    cell_styles: dict[tuple[int, int], TableCellStyle] = field(default_factory=dict)
    
    # Table width (percentage of available width or absolute points)
    width_percentage: Optional[float] = 100  # 100% of available width by default
    width_absolute: Optional[float] = None  # If set, overrides width_percentage
    
    # Row heights
    row_heights: Optional[list[float]] = None
    
    # Column widths (percentage of table width)
    column_widths: Optional[list[float]] = None
    
    # Table alignment on page
    alignment: HorizontalAlignment = HorizontalAlignment.LEFT
    
    # Table spacing
    space_before: float = 6
    space_after: float = 6
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "outer_border": self.outer_border.to_dict(),
            "inner_horizontal_border": self.inner_horizontal_border.to_dict(),
            "inner_vertical_border": self.inner_vertical_border.to_dict(),
            "header_style": self.header_style.to_dict(),
            "odd_row_style": self.odd_row_style.to_dict() if self.odd_row_style else None,
            "even_row_style": self.even_row_style.to_dict() if self.even_row_style else None,
            "column_styles": {str(k): v.to_dict() for k, v in self.column_styles.items()},
            "cell_styles": {f"{k[0]},{k[1]}": v.to_dict() for k, v in self.cell_styles.items()},
            "width_percentage": self.width_percentage,
            "width_absolute": self.width_absolute,
            "row_heights": self.row_heights,
            "column_widths": self.column_widths,
            "alignment": self.alignment.value,
            "space_before": self.space_before,
            "space_after": self.space_after
        }

# Predefined table styles
class TableStyles:
    """
    Collection of predefined table styles.
    """
    
    @staticmethod
    def default() -> TableStyle:
        """Default table style with light grid."""
        return TableStyle()
    
    @staticmethod
    def grid() -> TableStyle:
        """Strong grid lines for all cells."""
        return TableStyle(
            outer_border=Border(width=2.0),
            inner_horizontal_border=Border(width=1.0),
            inner_vertical_border=Border(width=1.0)
        )
    
    @staticmethod
    def no_grid() -> TableStyle:
        """No grid lines."""
        return TableStyle(
            outer_border=Border(width=0),
            inner_horizontal_border=Border(width=0),
            inner_vertical_border=Border(width=0)
        )
    
    @staticmethod
    def header_only() -> TableStyle:
        """Bold header row with line underneath, no other grid lines."""
        return TableStyle(
            outer_border=Border(width=0),
            inner_horizontal_border=Border(width=0),
            inner_vertical_border=Border(width=0),
            header_style=TableCellStyle(
                background_color=Color.LIGHT_GRAY,
                bold=True
            ),
            cell_styles={(0, -1): TableCellStyle(  # Bottom border of header row
                bold=True
            )}
        )
    
    @staticmethod
    def alternating_rows() -> TableStyle:
        """Alternating row colors with light gray background."""
        return TableStyle(
            outer_border=Border(width=1.0),
            inner_horizontal_border=Border(width=0.5),
            inner_vertical_border=Border(width=0.5),
            header_style=TableCellStyle(
                background_color=Color.DARK_GRAY,
                text_color=Color.WHITE,
                bold=True
            ),
            odd_row_style=TableCellStyle(),
            even_row_style=TableCellStyle(
                background_color=Color.LIGHT_GRAY
            )
        )
    
    @staticmethod
    def business() -> TableStyle:
        """Professional business style with navy header."""
        return TableStyle(
            outer_border=Border(width=1.0, color=Color.NAVY),
            inner_horizontal_border=Border(width=0.5, color=Color.NAVY),
            inner_vertical_border=Border(width=0.5, color=Color.NAVY),
            header_style=TableCellStyle(
                background_color=Color.NAVY,
                text_color=Color.WHITE,
                bold=True,
                horizontal_alignment=HorizontalAlignment.CENTER
            )
        )

@dataclass
class TextStyle:
    """
    Defines styling for text elements like paragraphs and headers.
    """
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    text_color: tuple[float, float, float] = Color.BLACK
    alignment: HorizontalAlignment = HorizontalAlignment.LEFT
    bold: bool = False
    italic: bool = False
    underline: bool = False
    line_spacing: float = 1.2
    space_before: float = 6
    space_after: float = 6
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "font_name": self.font_name,
            "font_size": self.font_size,
            "text_color": self.text_color,
            "alignment": self.alignment.value,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "line_spacing": self.line_spacing,
            "space_before": self.space_before,
            "space_after": self.space_after
        }

# Document template styles
@dataclass
class DocumentStyle:
    """
    Defines the overall style for a document.
    """
    # Title style
    title_style: TextStyle = field(default_factory=lambda: TextStyle(
        font_size=18,
        bold=True,
        space_after=12
    ))
    
    # Header styles
    h1_style: TextStyle = field(default_factory=lambda: TextStyle(
        font_size=16,
        bold=True,
        space_before=12,
        space_after=8
    ))
    
    h2_style: TextStyle = field(default_factory=lambda: TextStyle(
        font_size=14,
        bold=True,
        space_before=10,
        space_after=6
    ))
    
    h3_style: TextStyle = field(default_factory=lambda: TextStyle(
        font_size=12,
        bold=True,
        space_before=8,
        space_after=4
    ))
    
    # Paragraph style
    paragraph_style: TextStyle = field(default_factory=lambda: TextStyle(
        font_size=10,
        line_spacing=1.2
    ))
    
    # Default table style
    table_style: TableStyle = field(default_factory=TableStyles.default)
    
    # Page setup
    page_margins: tuple[float, float, float, float] = (72, 72, 72, 72)  # left, right, top, bottom (in points)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "title_style": self.title_style.to_dict(),
            "h1_style": self.h1_style.to_dict(),
            "h2_style": self.h2_style.to_dict(),
            "h3_style": self.h3_style.to_dict(),
            "paragraph_style": self.paragraph_style.to_dict(),
            "table_style": self.table_style.to_dict(),
            "page_margins": self.page_margins
        }

# Predefined document styles
class DocumentStyles:
    """
    Collection of predefined document styles.
    """
    
    @staticmethod
    def default() -> DocumentStyle:
        """Default document style."""
        return DocumentStyle()
    
    @staticmethod
    def business() -> DocumentStyle:
        """Professional business document style."""
        return DocumentStyle(
            title_style=TextStyle(
                font_size=20,
                bold=True,
                text_color=Color.NAVY,
                space_after=16
            ),
            h1_style=TextStyle(
                font_size=16,
                bold=True,
                text_color=Color.NAVY,
                space_before=14,
                space_after=10
            ),
            h2_style=TextStyle(
                font_size=14,
                bold=True,
                text_color=Color.NAVY,
                space_before=12,
                space_after=8
            ),
            h3_style=TextStyle(
                font_size=12,
                bold=True,
                text_color=Color.NAVY,
                space_before=10,
                space_after=6
            ),
            paragraph_style=TextStyle(
                font_size=10,
                line_spacing=1.3
            ),
            table_style=TableStyles.business()
        )
    
    @staticmethod
    def minimalist() -> DocumentStyle:
        """Clean, minimalist document style."""
        return DocumentStyle(
            title_style=TextStyle(
                font_size=24,
                bold=False,
                space_after=24
            ),
            h1_style=TextStyle(
                font_size=18,
                bold=False,
                space_before=18,
                space_after=12
            ),
            h2_style=TextStyle(
                font_size=14,
                bold=False,
                space_before=14,
                space_after=10
            ),
            h3_style=TextStyle(
                font_size=12,
                bold=False,
                italic=True,
                space_before=12,
                space_after=8
            ),
            paragraph_style=TextStyle(
                font_size=10,
                line_spacing=1.5
            ),
            table_style=TableStyles.no_grid()
        )
