"""
Tests for the DocumentTemplate feature in DocuForge.

These tests validate the functionality of document templates, including:
- Creating templates with placeholders
- Filling templates with values
- Template registry operations
- Serializing and deserializing templates
"""
import unittest
import json
from docuforge.templates import (
    DocumentTemplate, TemplatePlaceholder, template_registry,
    register_template, get_template
)
from docuforge.models import Section, DocumentData

class TestDocumentTemplates(unittest.TestCase):
    """Test cases for DocumentTemplate functionality."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Clear template registry before each test
        template_registry.clear()
        
        # Create test placeholders
        self.company_placeholder = TemplatePlaceholder(
            name="company_name",
            description="Company name",
            default_value="ACME Corp",
            required=True
        )
        
        self.address_placeholder = TemplatePlaceholder(
            name="address",
            description="Company address",
            default_value="123 Main St, Anytown, USA",
            required=False
        )
        
        # Create a test template
        self.report_template = DocumentTemplate(
            id="business_report",
            name="Business Report Template",
            description="A template for standard business reports",
            sections=[
                Section(
                    type="paragraph",
                    text="{{company_name}} - Business Report"
                ),
                Section(
                    type="paragraph",
                    text="Address: {{address}}"
                ),
                Section(
                    type="paragraph",
                    text="Date: {{report_date}}"
                ),
                Section(
                    type="table",
                    rows=[
                        ["Item", "Value", "Notes"],
                        ["Revenue", "{{revenue}}", "{{revenue_notes}}"],
                        ["Expenses", "{{expenses}}", "{{expense_notes}}"]
                    ]
                )
            ],
            placeholders=[
                self.company_placeholder,
                self.address_placeholder,
                TemplatePlaceholder(name="report_date", description="Report date", required=True),
                TemplatePlaceholder(name="revenue", description="Revenue figure", required=True),
                TemplatePlaceholder(name="revenue_notes", description="Revenue notes", required=False),
                TemplatePlaceholder(name="expenses", description="Expenses figure", required=True),
                TemplatePlaceholder(name="expense_notes", description="Expense notes", required=False)
            ]
        )

    def test_template_creation(self):
        """Test creating document templates with placeholders."""
        template = self.report_template
        self.assertEqual(template.id, "business_report")
        self.assertEqual(template.name, "Business Report Template")
        self.assertEqual(len(template.sections), 4)
        self.assertEqual(len(template.placeholders), 7)
        
        # Check placeholder extraction
        placeholders = template.extract_placeholders()
        self.assertIn("company_name", placeholders)
        self.assertIn("address", placeholders)
        self.assertIn("report_date", placeholders)
        self.assertIn("revenue", placeholders)
        self.assertIn("expenses", placeholders)

    def test_template_registration(self):
        """Test registering and retrieving templates from the registry."""
        # Register template
        register_template(self.report_template)
        
        # Retrieve template
        template = get_template("business_report")
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Business Report Template")
        
        # Test getting non-existent template
        missing = get_template("nonexistent")
        self.assertIsNone(missing)
        
        # Test registry size
        self.assertEqual(len(template_registry.templates), 1)

    def test_template_serialization(self):
        """Test serializing and deserializing templates to/from JSON."""
        # Test to_dict
        template_dict = self.report_template.to_dict()
        self.assertEqual(template_dict["id"], "business_report")
        self.assertEqual(template_dict["name"], "Business Report Template")
        self.assertIn("sections", template_dict)
        self.assertIn("placeholders", template_dict)
        
        # Test to_json
        template_json = self.report_template.to_json()
        parsed = json.loads(template_json)
        self.assertEqual(parsed["id"], "business_report")
        
        # Test from_dict
        new_template = DocumentTemplate.from_dict(template_dict)
        self.assertEqual(new_template.id, "business_report")
        self.assertEqual(new_template.name, "Business Report Template")
        self.assertEqual(len(new_template.sections), 4)
        self.assertEqual(len(new_template.placeholders), 7)
        
        # Test from_json
        json_template = DocumentTemplate.from_json(template_json)
        self.assertEqual(json_template.id, "business_report")
        self.assertEqual(json_template.name, "Business Report Template")

    def test_filling_template(self):
        """Test filling templates with values."""
        template = self.report_template
        
        # Fill with all required values
        filled_doc = template.fill({
            "company_name": "TechCorp Inc",
            "report_date": "2023-12-31",
            "revenue": "$1,000,000",
            "expenses": "$750,000"
        })
        
        self.assertEqual(filled_doc.title, "Business Report Template")  # Default title is template name
        self.assertEqual(len(filled_doc.sections), 4)
        self.assertEqual(filled_doc.sections[0].text, "TechCorp Inc - Business Report")
        self.assertEqual(filled_doc.sections[1].text, "Address: 123 Main St, Anytown, USA")  # Default value used
        self.assertEqual(filled_doc.sections[2].text, "Date: 2023-12-31")
        
        # Check table content
        table_rows = filled_doc.sections[3].rows
        self.assertEqual(table_rows[1][1], "$1,000,000")
        self.assertEqual(table_rows[2][1], "$750,000")
        
        # Fill with all values including non-required
        filled_doc = template.fill({
            "company_name": "TechCorp Inc",
            "address": "456 Tech Blvd, Silicon Valley, CA",
            "report_date": "2023-12-31",
            "revenue": "$1,000,000",
            "revenue_notes": "10% YoY growth",
            "expenses": "$750,000",
            "expense_notes": "5% below budget"
        })
        
        self.assertEqual(filled_doc.sections[1].text, "Address: 456 Tech Blvd, Silicon Valley, CA")
        table_rows = filled_doc.sections[3].rows
        self.assertEqual(table_rows[1][2], "10% YoY growth")
        self.assertEqual(table_rows[2][2], "5% below budget")

    def test_missing_required_values(self):
        """Test validation of required template values."""
        template = self.report_template
        
        # Missing required values should raise ValueError
        with self.assertRaises(ValueError):
            template.fill({
                "company_name": "TechCorp Inc",
                # Missing report_date
                "revenue": "$1,000,000",
                "expenses": "$750,000"
            })


if __name__ == "__main__":
    unittest.main()

