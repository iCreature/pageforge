# Changelog

All notable changes to DocuForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-07-04

### Added
- Initial release of DocuForge
- Core PDF document generation functionality
- Multiple section types support (paragraph, table, header, footer, list, heading)
- Image embedding as XObjects
- Template system with fragments and placeholders
- Registry for templates and fragments
- Flexible styling system
- ReportLab rendering engine
- WeasyPrint engine support
- International text support
- Font detection and fallback system

### Fixed
- Fragment registry retrieval by both ID and name
- Template registry retrieval by both ID and name
- Proper serialization of template style attribute
- Support for heading section type with level attribute
- Fixed test coverage and dependencies issues

