"""
Tests for the DocumentTemplate feature in PageForge.

These tests validate the functionality of document templates, including:
- Creating templates with placeholders
- Filling templates with values
- Template registry operations
- Serializing and deserializing templates
"""
import json
import unittest

from pageforge.core.models import Section
from pageforge.templating.templates import (
    DocumentTemplate,
    TemplatePlaceholder,
    get_template,
    register_template,
    template_registry,
)


class TestDocumentTemplates(unittest.TestCase):
    """Test cases for DocumentTemplate functionality."""
    
    def setUp(self):
        """Set up test cases."""
        # Clear template registry before each test
        template_registry.clear()
    
    def test_template_creation(self):
        """Test creation of document templates."""
        # Create a simple template
        sections = [
            Section(type="paragraph", text="Hello, {{name}}!"),
            Section(type="heading", text="Welcome to {{company}}", level=1)
        ]
        template = DocumentTemplate(
            name="welcome-template",
            title="Welcome Document for {{name}}",
            sections=sections,
            placeholders=[
                TemplatePlaceholder(name="name", description="Recipient name"),
                TemplatePlaceholder(name="company", description="Company name")
            ]
        )
        
        self.assertEqual(template.name, "welcome-template")
        self.assertEqual(template.title, "Welcome Document for {{name}}")
        self.assertEqual(len(template.sections), 2)
        self.assertEqual(len(template.placeholders), 2)
    
    def test_template_fill(self):
        """Test filling templates with values."""
        sections = [
            Section(type="paragraph", text="Hello, {{name}}!"),
            Section(type="paragraph", text="Welcome to {{company}}.")
        ]
        template = DocumentTemplate(
            name="fill-template",
            title="Welcome to {{company}}",
            sections=sections,
            placeholders=[
                TemplatePlaceholder(name="name", description="Recipient name"),
                TemplatePlaceholder(name="company", description="Company name")
            ]
        )
        
        # Fill template with values
        values = {"name": "John", "company": "PageForge"}
        document = template.fill(values)
        
        self.assertEqual(document.title, "Welcome to PageForge")
        self.assertEqual(document.sections[0].text, "Hello, John!")
        self.assertEqual(document.sections[1].text, "Welcome to PageForge.")
    
    def test_template_registration(self):
        """Test registration and retrieval of templates."""
        template = DocumentTemplate(
            name="registration-test",
            title="Test Template",
            sections=[],
            placeholders=[]
        )
        register_template(template)
        
        # Retrieve the template
        retrieved = get_template("registration-test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "registration-test")
        
        # Test retrieving non-existent template
        with self.assertRaises(KeyError):
            get_template("non-existent")
    
    def test_template_serialization(self):
        """Test serialization and deserialization of templates."""
        template = DocumentTemplate(
            name="serialization-test",
            title="Test Template {{name}}",
            sections=[
                Section(type="paragraph", text="Hello, {{name}}!")
            ],
            placeholders=[
                TemplatePlaceholder(name="name", description="Recipient name")
            ]
        )
        
        # Serialize to JSON
        json_data = template.to_json()
        json_dict = json.loads(json_data)
        
        self.assertEqual(json_dict["name"], "serialization-test")
        self.assertEqual(json_dict["title"], "Test Template {{name}}")
        
        # Deserialize from JSON
        new_template = DocumentTemplate.from_json(json_data)
        self.assertEqual(new_template.name, template.name)
        self.assertEqual(new_template.title, template.title)
        self.assertEqual(len(new_template.placeholders), 1)
        self.assertEqual(new_template.placeholders[0].name, "name")

if __name__ == "__main__":
    unittest.main()
