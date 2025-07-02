"""
Tests for the DocumentFragment feature in DocuForge.

These tests validate the functionality of document fragments, including:
- Creating and registering fragments
- Using fragments within documents
- Serializing and deserializing fragments
- Fragment registry operations
"""
import unittest
import json
from docuforge.fragments import (
    DocumentFragment, fragment_registry, register_fragment, get_fragment
)
from docuforge.models import Section, DocumentData

class TestDocumentFragments(unittest.TestCase):
    """Test cases for DocumentFragment functionality."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Clear fragment registry before each test
        fragment_registry.clear()
        
        # Create some test fragments
        self.disclaimer_fragment = DocumentFragment(
            id="legal_disclaimer",
            name="Legal Disclaimer",
            sections=[
                Section(
                    type="paragraph",
                    text="This document is for informational purposes only and does not constitute legal advice."
                )
            ],
            meta={
                "category": "legal",
                "show_header": True
            }
        )
        
        self.contact_fragment = DocumentFragment(
            id="contact_info",
            name="Contact Information",
            sections=[
                Section(
                    type="paragraph",
                    text="Email: info@example.com\nPhone: (555) 123-4567"
                )
            ]
        )

    def test_fragment_creation(self):
        """Test creating document fragments with various attributes."""
        # Test basic properties
        fragment = self.disclaimer_fragment
        self.assertEqual(fragment.id, "legal_disclaimer")
        self.assertEqual(fragment.name, "Legal Disclaimer")
        self.assertEqual(len(fragment.sections), 1)
        self.assertEqual(fragment.sections[0].text, 
                        "This document is for informational purposes only and does not constitute legal advice.")
        self.assertEqual(fragment.meta["category"], "legal")
        
        # Test fragment with no metadata
        fragment = DocumentFragment(id="simple", name="Simple Fragment", sections=[])
        self.assertEqual(fragment.meta, {})

    def test_fragment_registration(self):
        """Test registering and retrieving fragments from the registry."""
        # Register fragments
        register_fragment(self.disclaimer_fragment)
        register_fragment(self.contact_fragment)
        
        # Retrieve fragments
        disclaimer = get_fragment("legal_disclaimer")
        contact = get_fragment("contact_info")
        
        self.assertIsNotNone(disclaimer)
        self.assertIsNotNone(contact)
        self.assertEqual(disclaimer.name, "Legal Disclaimer")
        self.assertEqual(contact.name, "Contact Information")
        
        # Test getting non-existent fragment
        missing = get_fragment("nonexistent")
        self.assertIsNone(missing)
        
        # Test registry size
        self.assertEqual(len(fragment_registry.fragments), 2)

    def test_fragment_serialization(self):
        """Test serializing and deserializing fragments to/from JSON."""
        # Test to_dict
        fragment_dict = self.disclaimer_fragment.to_dict()
        self.assertEqual(fragment_dict["id"], "legal_disclaimer")
        self.assertEqual(fragment_dict["name"], "Legal Disclaimer")
        self.assertIn("sections", fragment_dict)
        self.assertIn("meta", fragment_dict)
        
        # Test to_json
        fragment_json = self.disclaimer_fragment.to_json()
        parsed = json.loads(fragment_json)
        self.assertEqual(parsed["id"], "legal_disclaimer")
        
        # Test from_dict
        new_fragment = DocumentFragment.from_dict(fragment_dict)
        self.assertEqual(new_fragment.id, "legal_disclaimer")
        self.assertEqual(new_fragment.name, "Legal Disclaimer")
        self.assertEqual(len(new_fragment.sections), 1)
        
        # Test from_json
        json_fragment = DocumentFragment.from_json(fragment_json)
        self.assertEqual(json_fragment.id, "legal_disclaimer")
        self.assertEqual(json_fragment.name, "Legal Disclaimer")

    def test_using_fragments_in_document(self):
        """Test using fragments within a document."""
        # Register fragment
        register_fragment(self.disclaimer_fragment)
        
        # Create document with fragment
        doc = DocumentData(
            title="Test Document",
            sections=[
                Section(
                    type="paragraph", 
                    text="This is a test document."
                ),
                Section(
                    type="fragment",
                    fragment_id="legal_disclaimer"
                )
            ]
        )
        
        # Check document structure
        self.assertEqual(len(doc.sections), 2)
        self.assertEqual(doc.sections[0].type, "paragraph")
        self.assertEqual(doc.sections[1].type, "fragment")
        self.assertEqual(doc.sections[1].fragment_id, "legal_disclaimer")
        
        # Use the new add_fragment convenience method
        doc.add_fragment("legal_disclaimer")
        self.assertEqual(len(doc.sections), 3)
        self.assertEqual(doc.sections[2].type, "fragment")
        self.assertEqual(doc.sections[2].fragment_id, "legal_disclaimer")


if __name__ == "__main__":
    unittest.main()
