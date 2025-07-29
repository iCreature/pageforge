# Introduction to PageForge

PageForge is a powerful document generation library designed to create professional PDFs with consistent styling, logo placement, and proper page numbering. It's built to be easy to use while offering powerful customization options.

## Core Philosophy

PageForge is built on several key principles:

1. **Simplicity**: Create professional documents with minimal code
2. **Consistency**: Ensure logos, headers, and footers appear consistently across pages
3. **Flexibility**: Support various document types and content structures
4. **Integration**: Seamlessly work with LLM-generated content

## Key Features

### Single Logo Support

PageForge allows you to include a single logo image consistently positioned on every page. The current implementation supports:

- PNG, JPG/JPEG image formats
- Maximum file size of 2MB
- Top-right corner positioning by default (customizable)
- Consistent rendering across all pages

### Page Numbering

Documents can include dynamic page numbering in the footer, with placeholders that are automatically replaced:

- `{page_number}`: Current page number
- `{total_pages}`: Total number of pages

### Document Structure

PageForge supports a variety of content sections:

- Headers and titles
- Paragraphs with formatted text
- Tables with customizable styling
- Bulleted and numbered lists
- Footer text with dynamic page numbers

### Multiple Interfaces

- **API Mode**: Generate documents programmatically
- **CLI Mode**: Create documents from the command line
- **LLM Integration**: Accept structured content from language models

## Design Principles

PageForge follows SOLID principles:

- **Single Responsibility**: Each class has a focused purpose
- **Open/Closed**: Extend functionality without modifying core code
- **Liskov Substitution**: Components are interchangeable through interfaces
- **Interface Segregation**: Focused interfaces for specific functionality
- **Dependency Inversion**: Depend on abstractions, not implementations

Design patterns used include Strategy Pattern for logo positioning and Factory Pattern for document generation.
