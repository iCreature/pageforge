"""
Document fragments module for DocuForge.

This module provides a way to create, manage, and reuse document fragments.
Fragments are reusable pieces of content that can be included in multiple documents.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json

from ..core.models import Section
from ..rendering.styles import TextStyle, TableStyle
from ..core.exceptions import ValidationError


@dataclass
class DocumentFragment:
    """
    A reusable document fragment that can be included in multiple documents.
    
    Document fragments are self-contained content pieces that can be reused across
    different documents. Each fragment has a unique ID, a name, and contains one
    or more sections.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier
    name: str = "Unnamed Fragment"  # Human-readable name
    description: str = ""  # Description of the fragment
    sections: List[Section] = field(default_factory=list)  # Content sections
    meta: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sections": [s.__dict__ for s in self.sections],
            "meta": self.meta
        }
        
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DocumentFragment':
        """Create a fragment from a dictionary representation."""
        sections = []
        for section_data in data.get("sections", []):
            section = Section(
                type=section_data.get("type"),
                rows=section_data.get("rows"),
                text=section_data.get("text"),
                items=section_data.get("items"),
                data=section_data.get("data", {})
            )
            sections.append(section)
            
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Unnamed Fragment"),
            description=data.get("description", ""),
            sections=sections,
            meta=data.get("meta", {})
        )
    
    def save(self, file_path: str) -> None:
        """Save the fragment to a JSON file."""
        fragment_data = self.to_dict()
        with open(file_path, 'w') as f:
            json.dump(fragment_data, f, indent=2)
    
    @classmethod
    def load(cls, file_path: str) -> 'DocumentFragment':
        """Load a fragment from a JSON file."""
        with open(file_path, 'r') as f:
            fragment_data = json.load(f)
        return cls.from_dict(fragment_data)


class FragmentRegistry:
    """
    Registry for managing document fragments.
    
    This class provides a centralized repository for storing, retrieving,
    and managing document fragments.
    """
    def __init__(self):
        self.fragments: Dict[str, DocumentFragment] = {}
    
    def register_fragment(self, fragment: DocumentFragment) -> None:
        """Register a fragment in the registry."""
        self.fragments[fragment.id] = fragment
    
    def get_fragment(self, fragment_id: str) -> Optional[DocumentFragment]:
        """Get a fragment by its ID."""
        return self.fragments.get(fragment_id)
    
    def list_fragments(self) -> List[Dict[str, str]]:
        """List all registered fragments with basic metadata."""
        return [
            {"id": f.id, "name": f.name, "description": f.description}
            for f in self.fragments.values()
        ]
    
    def remove_fragment(self, fragment_id: str) -> bool:
        """Remove a fragment from the registry."""
        if fragment_id in self.fragments:
            del self.fragments[fragment_id]
            return True
        return False
        
    def clear(self) -> None:
        """Clear all fragments from the registry."""
        self.fragments.clear()


# Global fragment registry
fragment_registry = FragmentRegistry()


# Create some common fragments
def create_default_fragments() -> None:
    """Create and register default fragments."""
    # Legal disclaimer fragment
    legal_disclaimer = DocumentFragment(
        name="Legal Disclaimer",
        description="Standard legal disclaimer for documents",
        sections=[
            Section(
                type="paragraph",
                text="DISCLAIMER: This document is provided for informational purposes only. "
                     "The information contained herein is subject to change without notice and "
                     "is not warranted to be error-free. If you find any errors, please report them "
                     "to us in writing."
            )
        ],
        meta={"category": "legal", "version": "1.0"}
    )
    
    # Contact information fragment
    contact_info = DocumentFragment(
        name="Contact Information",
        description="Company contact information block",
        sections=[
            Section(
                type="paragraph",
                text="Contact Us:\nPhone: (555) 123-4567\nEmail: info@example.com\n"
                     "Website: www.example.com\nAddress: 123 Main St, Anytown, USA 12345"
            )
        ],
        meta={"category": "contact", "version": "1.0"}
    )
    
    # Terms and conditions fragment
    terms = DocumentFragment(
        name="Terms and Conditions",
        description="Standard terms and conditions section",
        sections=[
            Section(type="header", text="Terms and Conditions"),
            Section(
                type="paragraph",
                text="1. All content must be used in accordance with applicable laws.\n"
                     "2. Pricing is subject to change without notice.\n"
                     "3. Payment is due within 30 days of invoice date.\n"
                     "4. Late payments are subject to a 1.5% monthly fee.\n"
                     "5. All sales are final."
            )
        ],
        meta={"category": "legal", "version": "1.0"}
    )
    
    # Executive summary fragment
    executive_summary = DocumentFragment(
        name="Executive Summary Template",
        description="Template for an executive summary section",
        sections=[
            Section(type="header", text="Executive Summary"),
            Section(
                type="paragraph",
                text="This report provides an overview of [topic]. The key findings indicate "
                     "that [main finding]. Based on these findings, we recommend [recommendation]."
            )
        ],
        meta={"category": "business", "version": "1.0"}
    )
    
    # Register the fragments
    fragment_registry.register_fragment(legal_disclaimer)
    fragment_registry.register_fragment(contact_info)
    fragment_registry.register_fragment(terms)
    fragment_registry.register_fragment(executive_summary)


# Helper functions for working with fragments
def register_fragment(fragment: DocumentFragment) -> None:
    """Register a fragment in the global registry."""
    fragment_registry.register_fragment(fragment)


def get_fragment(fragment_id: str) -> DocumentFragment:
    """Get a fragment from the global registry.
    
    Args:
        fragment_id: The ID of the fragment to retrieve
        
    Returns:
        The requested fragment
        
    Raises:
        KeyError: If the fragment does not exist
    """
    fragment = fragment_registry.get_fragment(fragment_id)
    if fragment is None:
        raise KeyError(f"Fragment with ID '{fragment_id}' not found")
    return fragment
