"""
Tests for the DocumentFragment feature in PageForge.

These tests validate the functionality of document fragments, including:
- Creating and registering fragments
- Using fragments within documents
- Serializing and deserializing fragments
- Fragment registry operations
"""
import json
import unittest

from pageforge.core.models import Section
from pageforge.templating.fragments import (
    DocumentFragment,
    fragment_registry,
    get_fragment,
    register_fragment,
)


class TestDocumentFragments(unittest.TestCase):
    """Test cases for DocumentFragment functionality."""

    def setUp(self):
        """Set up test cases."""
        # Clear fragment registry before each test
        fragment_registry.clear()
    
    def test_fragment_creation(self):
        """Test creation of document fragments."""
        # Create a simple fragment
        sections = [
            Section(type="paragraph", text="This is a test paragraph."),
            Section(type="heading", text="Test Heading", level=2)
        ]
        fragment = DocumentFragment(name="test-fragment", sections=sections)
        
        self.assertEqual(fragment.name, "test-fragment")
        self.assertEqual(len(fragment.sections), 2)
        self.assertEqual(fragment.sections[0].type, "paragraph")
        self.assertEqual(fragment.sections[1].type, "heading")
    
    def test_fragment_registration(self):
        """Test registration and retrieval of fragments."""
        # Create and register a fragment
        sections = [Section(type="paragraph", text="Test content")]
        fragment = DocumentFragment(name="test-register", sections=sections)
        register_fragment(fragment)
        
        # Retrieve the fragment
        retrieved = get_fragment("test-register")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "test-register")
        self.assertEqual(len(retrieved.sections), 1)
        
        # Test retrieving non-existent fragment
        with self.assertRaises(KeyError):
            get_fragment("non-existent")
    
    def test_fragment_serialization(self):
        """Test serialization and deserialization of fragments."""
        sections = [
            Section(type="paragraph", text="Serialization test"),
            Section(type="list", items=["Item 1", "Item 2"])
        ]
        fragment = DocumentFragment(name="serialization-test", sections=sections)
        
        # Serialize to JSON
        json_data = fragment.to_json()
        json_dict = json.loads(json_data)
        
        self.assertEqual(json_dict["name"], "serialization-test")
        self.assertEqual(len(json_dict["sections"]), 2)
        
        # Deserialize from JSON
        new_fragment = DocumentFragment.from_json(json_data)
        self.assertEqual(new_fragment.name, fragment.name)
        self.assertEqual(len(new_fragment.sections), len(fragment.sections))
        self.assertEqual(new_fragment.sections[0].text, "Serialization test")

if __name__ == "__main__":
    unittest.main()
