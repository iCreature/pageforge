"""
Document templates system for PageForge.

This module provides a template system for document reuse, allowing users to create
template documents that can be filled with specific content. Templates define the structure,
styling, and static content of documents, while placeholders allow for dynamic content insertion.
"""

import copy
import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from ..core.exceptions import ValidationError
from ..core.models import DocumentData, Section
from ..rendering.styles import DocumentStyle, DocumentStyles


@dataclass
class TemplatePlaceholder:
    """
    Represents a placeholder in a document template that can be filled with content.
    
    Placeholders can be in section text, table cells, or other document components.
    They're identified with a special syntax like {{placeholder_name}}.
    """
    name: str  # Unique identifier for this placeholder
    description: str = ""  # Human-readable description of what should go here
    default_value: Optional[Any] = None  # Default value if none provided
    required: bool = False  # Whether this placeholder must be filled
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "default_value": self.default_value,
            "required": self.required
        }


@dataclass
class DocumentTemplate:
    """
    Document template for reuse across multiple documents.
    
    A template defines the structure and static content of a document, with placeholders
    for dynamic content that can be filled at render time.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier
    name: str = "Untitled Template"  # Human-readable template name
    title: str = ""  # Template title with potential placeholders
    description: str = ""  # Description of the template
    document: DocumentData = None  # Base document structure with placeholders
    style: DocumentStyle = field(default_factory=DocumentStyles.default)  # Default document style
    sections: list[Section] = field(default_factory=list)  # Content sections
    placeholders: list[TemplatePlaceholder] = field(default_factory=list)  # Available placeholders
    _placeholders_dict: dict[str, TemplatePlaceholder] = field(default_factory=dict, repr=False)  # Internal placeholder mapping
    
    def __init__(self, name: str, sections: list[Section] = None, placeholders: list[TemplatePlaceholder] = None, 
                 title: str = None, description: str = "", id: str = None, style: DocumentStyle = None):
        """Initialize a document template with the given parameters."""
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.sections = sections or []
        self.placeholders = placeholders or []
        self._placeholders_dict = {}
        self.style = style or DocumentStyles.default()
        
        # Set title attribute
        self.title = title or name
        
        # Create document with the title and sections
        self.document = DocumentData(title=self.title)
        if sections:
            self.document.sections = copy.deepcopy(sections)
            
        # Build the placeholders dictionary
        for placeholder in self.placeholders:
            self._placeholders_dict[placeholder.name] = placeholder
            
        self._extract_placeholders()
    
    def _extract_placeholders(self) -> None:
        """Extract all placeholders from the document content."""
        # Extract from title
        self._extract_placeholders_from_text(self.document.title, "title")
        
        # Extract from sections
        for section in self.document.sections:
            if section.text:
                self._extract_placeholders_from_text(section.text, f"section_{section.type}")
            
            # Extract from tables
            if section.type == "table" and section.rows:
                for i, row in enumerate(section.rows):
                    for j, cell in enumerate(row):
                        if isinstance(cell, str):
                            self._extract_placeholders_from_text(cell, f"table_cell_{i}_{j}")
            
            # Extract from lists
            if section.type == "list" and section.items:
                for i, item in enumerate(section.items):
                    if isinstance(item, str):
                        self._extract_placeholders_from_text(item, f"list_item_{i}")
    
    def _extract_placeholders_from_text(self, text: str, context: str) -> None:
        """Extract placeholders from text using regex pattern {{placeholder_name}}."""
        if not isinstance(text, str):
            return
            
        # Find all instances of {{placeholder_name}}
        pattern = r"{{([^{}]+)}}"
        matches = re.findall(pattern, text)
        
        for match in matches:
            name = match.strip()
            if name not in self._placeholders_dict:
                placeholder = TemplatePlaceholder(
                    name=name,
                    description=f"Placeholder in {context}",
                    required=False
                )
                self.placeholders.append(placeholder)
                self._placeholders_dict[name] = placeholder
    
    def fill(self, values: dict[str, Any]) -> DocumentData:
        """
        Fill the template with provided values and return a complete DocumentData object.
        
        Args:
            values: Dictionary mapping placeholder names to their values
            
        Returns:
            A new DocumentData instance with placeholders filled with values
            
        Raises:
            ValidationError: If required placeholders are missing
        """
        # Check for required placeholders
        missing = []
        for placeholder in self.placeholders:
            if placeholder.required and placeholder.name not in values:
                missing.append(placeholder.name)
        
        if missing:
            raise ValidationError(
                message="Missing required template values",
                details={
                    "missing_placeholders": missing,
                    "template_name": self.name
                }
            )
        
        # Create a new document with filled values
        filled_doc = DocumentData(title=self._fill_text(self.document.title, values))
        
        # Add filled sections from template
        if self.document.sections:
            filled_doc.sections = []
            for section in self.document.sections:
                filled_section = copy.deepcopy(section)
                if filled_section.text:
                    filled_section.text = self._fill_text(filled_section.text, values)
                filled_doc.sections.append(filled_section)
        # If no sections in document, try using the template's sections directly
        elif self.sections:
            filled_doc.sections = []
            for section in self.sections:
                filled_section = copy.deepcopy(section)
                if filled_section.text:
                    filled_section.text = self._fill_text(filled_section.text, values)
                filled_doc.sections.append(filled_section)
        
        # Fill sections
        for section in filled_doc.sections:
            if section.text:
                section.text = self._fill_text(section.text, values)
            
            # Fill tables
            if section.type == "table" and section.rows:
                for i, row in enumerate(section.rows):
                    for j, cell in enumerate(row):
                        if isinstance(cell, str):
                            section.rows[i][j] = self._fill_text(cell, values)
            
            # Fill lists
            if section.type == "list" and section.items:
                for i, item in enumerate(section.items):
                    if isinstance(item, str):
                        section.items[i] = self._fill_text(item, values)
        
        return filled_doc
    
    def _fill_text(self, text: str, values: dict[str, Any]) -> str:
        """Replace placeholders in text with their values."""
        if not isinstance(text, str):
            return text
            
        # Replace all instances of {{placeholder_name}} with values
        pattern = r"{{([^{}]+)}}"
        
        def replace_match(match):
            name = match.group(1).strip()
            if name in values:
                return str(values[name])
            elif name in self._placeholders_dict and self._placeholders_dict[name].default_value is not None:
                return str(self._placeholders_dict[name].default_value)
            else:
                return match.group(0)  # Keep placeholder if no value available
        
        return re.sub(pattern, replace_match, text)
    
    def to_dict(self) -> dict:
        """Convert template to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "sections": [section.__dict__ for section in self.sections],
            "placeholders": [placeholder.to_dict() for placeholder in self.placeholders],
            "style": self.style.to_dict() if self.style else None
        }
    
    def to_json(self) -> str:
        """Convert template to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DocumentTemplate':
        """Create a template from a dictionary representation."""
        # Parse sections
        sections = []
        for section_data in data.get("sections", []):
            section = Section(
                type=section_data.get("type"),
                rows=section_data.get("rows"),
                text=section_data.get("text"),
                items=section_data.get("items"),
                data=section_data.get("data", {}),
                level=section_data.get("level")
            )
            sections.append(section)
        
        # Parse placeholders
        placeholders = []
        for ph_data in data.get("placeholders", []):
            placeholder = TemplatePlaceholder(
                name=ph_data.get("name", ""),
                description=ph_data.get("description", ""),
                default_value=ph_data.get("default_value"),
                required=ph_data.get("required", False)
            )
            placeholders.append(placeholder)
        
        # Create the template
        return cls(
            id=data.get("id"),
            name=data.get("name", "Untitled Template"),
            title=data.get("title"),
            description=data.get("description", ""),
            sections=sections,
            placeholders=placeholders
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DocumentTemplate':
        """Create a template from a JSON string."""
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        return cls.from_dict(data)
    
    def save(self, file_path: str) -> None:
        """Save the template to a JSON file."""
        template_data = self.to_dict()
        with open(file_path, 'w') as f:
            json.dump(template_data, f, indent=2)
    
    @classmethod
    def load(cls, file_path: str) -> 'DocumentTemplate':
        """Load a template from a JSON file."""
        with open(file_path) as f:
            template_data = json.load(f)
        return cls.from_dict(template_data)


class TemplateRegistry:
    """
    Registry for managing document templates.
    
    This class provides a centralized repository for storing, retrieving,
    and managing document templates.
    """
    def __init__(self):
        self.templates: dict[str, DocumentTemplate] = {}
    
    def register_template(self, template: DocumentTemplate) -> None:
        """Register a template in the registry."""
        self.templates[template.id] = template
    
    def get_template(self, template_id_or_name: str) -> Optional[DocumentTemplate]:
        """Get a template by its ID or name.
        
        Args:
            template_id_or_name: The ID or name of the template to retrieve
            
        Returns:
            The template with the given ID or name, or None if not found
        """
        # First try by ID
        if template_id_or_name in self.templates:
            return self.templates[template_id_or_name]
            
        # Then try by name
        for template in self.templates.values():
            if template.name == template_id_or_name:
                return template
                
        return None
    
    def list_templates(self) -> list[dict[str, str]]:
        """List all registered templates with basic metadata."""
        return [
            {"id": t.id, "name": t.name, "description": t.description}
            for t in self.templates.values()
        ]
    
    def remove_template(self, template_id: str) -> bool:
        """Remove a template from the registry."""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False
        
    def clear(self) -> None:
        """Clear all templates from the registry."""
        self.templates.clear()


# Global template registry
template_registry = TemplateRegistry()


# Create a few common templates
def create_default_templates() -> None:
    """Create and register default templates."""
    # Basic report template
    basic_report = DocumentTemplate(
        name="Basic Report",
        description="A simple report template with title, introduction, and content sections",
        document=DocumentData(
            title="{{report_title}}",
            sections=[
                Section(type="paragraph", text="{{introduction}}"),
                Section(type="header", text="Key Findings"),
                Section(type="paragraph", text="{{key_findings}}"),
                Section(type="header", text="Details"),
                Section(type="paragraph", text="{{details}}"),
                Section(type="header", text="Conclusion"),
                Section(type="paragraph", text="{{conclusion}}")
            ]
        )
    )
    basic_report.placeholders["report_title"] = TemplatePlaceholder(
        name="report_title",
        description="Title of the report",
        default_value="Report",
        required=True
    )
    basic_report.placeholders["introduction"] = TemplatePlaceholder(
        name="introduction",
        description="Introduction paragraph",
        required=True
    )
    basic_report.placeholders["key_findings"] = TemplatePlaceholder(
        name="key_findings",
        description="Summary of key findings",
        required=True
    )
    basic_report.placeholders["details"] = TemplatePlaceholder(
        name="details",
        description="Detailed explanation",
        required=True
    )
    basic_report.placeholders["conclusion"] = TemplatePlaceholder(
        name="conclusion",
        description="Conclusion paragraph",
        required=True
    )
    
    # Invoice template
    invoice_template = DocumentTemplate(
        name="Invoice",
        description="A basic invoice template with customer details and line items",
        document=DocumentData(
            title="Invoice #{{invoice_number}}",
            sections=[
                Section(type="paragraph", text="Date: {{invoice_date}}"),
                Section(type="paragraph", text="Due Date: {{due_date}}"),
                Section(type="header", text="Bill To:"),
                Section(type="paragraph", text="{{customer_name}}\n{{customer_address}}"),
                Section(type="header", text="Line Items:"),
                Section(
                    type="table",
                    rows=[
                        ["Description", "Quantity", "Unit Price", "Amount"],
                        ["{{item1_description}}", "{{item1_quantity}}", "{{item1_price}}", "{{item1_amount}}"],
                        ["{{item2_description}}", "{{item2_quantity}}", "{{item2_price}}", "{{item2_amount}}"]
                    ]
                ),
                Section(type="paragraph", text="Subtotal: {{subtotal}}"),
                Section(type="paragraph", text="Tax: {{tax}}"),
                Section(type="paragraph", text="Total: {{total}}"),
                Section(type="paragraph", text="Thank you for your business!")
            ]
        )
    )
    
    # Business letter template
    business_letter = DocumentTemplate(
        name="Business Letter",
        description="A formal business letter template",
        document=DocumentData(
            title="{{subject}}",
            sections=[
                Section(type="paragraph", text="{{sender_address}}"),
                Section(type="paragraph", text="{{date}}"),
                Section(type="paragraph", text="{{recipient_name}}\n{{recipient_address}}"),
                Section(type="paragraph", text="Dear {{salutation}},"),
                Section(type="paragraph", text="{{body_text}}"),
                Section(type="paragraph", text="Sincerely,"),
                Section(type="paragraph", text="{{sender_name}}\n{{sender_title}}")
            ]
        )
    )
    
    # Register the templates
    template_registry.register_template(basic_report)
    template_registry.register_template(invoice_template)
    template_registry.register_template(business_letter)


# Helper functions for working with templates
def register_template(template: DocumentTemplate) -> None:
    """Register a template in the global registry."""
    template_registry.register_template(template)


def get_template(template_id_or_name: str) -> DocumentTemplate:
    """Get a template from the global registry by ID or name.
    
    Args:
        template_id_or_name: The ID or name of the template to retrieve
        
    Returns:
        The requested template
        
    Raises:
        KeyError: If the template does not exist
    """
    template = template_registry.get_template(template_id_or_name)
    if template is None:
        raise KeyError(f"Template with ID or name '{template_id_or_name}' not found")
    return template
