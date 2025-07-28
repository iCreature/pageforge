# Changelog

All notable changes to PageForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-07-20

### Added
- Initial release of PageForge
- Core PDF document generation functionality
- Multiple section types support (paragraph, table, header, footer, list, heading)
- Image embedding as XObjects
- Template system with fragments and placeholders
- Registry for templates and fragments
- Flexible styling system
- ReportLab rendering engine
- WeasyPrint engine support (as optional extra)
- International text support
- Font detection and fallback system
- Command-line interface with version reporting
- Modern PEP 621 compliant packaging with pyproject.toml
- Dynamic versioning using setuptools-scm
- Complete type hints with py.typed marker
- GitHub Actions workflows for testing and deployment

### Fixed
- Fragment registry retrieval by both ID and name
- Template registry retrieval by both ID and name
- Proper serialization of template style attribute
- Support for heading section type with level attribute
- Fixed test coverage and dependencies issues

