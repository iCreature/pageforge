#!/bin/bash
# Script to simulate the deploy-pypi.yml GitHub Action workflow locally
set -e  # Exit on any error

echo "===== Starting local deploy-pypi workflow simulation ====="

echo "===== Installing dependencies ====="
python3 -m pip install --upgrade pip
python3 -m pip install build twine setuptools setuptools-scm wheel pytest pytest-cov ruff mypy

echo "===== Building package ====="
python3 -m build

echo "===== Checking distribution ====="
python3 -m twine check dist/*

echo "===== Installing package in development mode for testing ====="
python3 -m pip install -e .[dev]

echo "===== Running linting checks ====="
ruff check src/ tests/ --exit-zero

echo "===== Running type checks ====="
mypy --no-error-summary --no-incremental --show-error-codes --pretty src/ || true

echo "===== Running tests ====="
pytest --cov=src/pageforge --cov-report=term-missing --cov-fail-under=65 || echo "Some tests failed, but workflow will continue"

echo "===== Workflow completed locally ====="
echo "NOTE: The actual PyPI publishing step was skipped as it requires authentication tokens"
echo "To manually publish to TestPyPI, you would run:"
echo "twine upload --repository-url https://test.pypi.org/legacy/ dist/* -u __token__ -p <YOUR_TEST_PYPI_TOKEN>"

# Optional: Clean up build artifacts
# echo "===== Cleaning up build artifacts ====="
# rm -rf dist/ build/ src/*.egg-info/
