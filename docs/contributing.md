# Contributing to PageForge

Thank you for your interest in contributing to PageForge! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pageforge.git
   cd pageforge
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

### Branching Strategy

- `main`: Stable release branch
- `develop`: Development branch for ongoing work
- Feature branches: Create from `develop` using format `feature/feature-name`
- Bug fix branches: Create from `main` using format `fix/bug-name`

### Making Changes

1. Create a new branch from `develop` for your feature:
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit with meaningful messages:
   ```bash
   git commit -m "feat: add new feature for X"
   ```
   
   We follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

3. Push your branch and create a Pull Request against `develop`.

### Testing

Run tests to ensure your changes don't break existing functionality:

```bash
pytest
```

For test coverage report:

```bash
pytest --cov=src/pageforge --cov-report=term
```

### Code Style

We follow PEP 8 style guidelines. Run linting before committing:

```bash
flake8 src/ tests/
```

## Pull Request Guidelines

1. Update documentation if you're changing functionality
2. Include tests for new features
3. Update the CHANGELOG.md file if appropriate
4. Make sure all tests pass before submitting
5. Reference any related issues in your PR description

## Documentation

When adding new features, please update the documentation:

1. Add docstrings to new functions, classes, and methods
2. Update or add examples in the `docs/examples.md` file
3. Update API documentation in `docs/api.md` if you've changed the public API

To build the documentation locally:

```bash
cd docs
pip install -r requirements.txt
make html
```

Then open `docs/_build/html/index.html` in your browser.

## Release Process

1. Ensure all tests pass on `develop`
2. Update version in `src/pageforge/__init__.py`
3. Update CHANGELOG.md
4. Merge `develop` into `main`
5. Tag the release: `git tag v0.1.0`
6. Push the tag: `git push origin v0.1.0`
7. Create a new release on GitHub

## Code of Conduct

Please be respectful and inclusive in your interactions with other contributors. We aim to foster an open and welcoming environment for everyone.

## License

By contributing to PageForge, you agree that your contributions will be licensed under the project's MIT License.
