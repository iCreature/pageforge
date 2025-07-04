from setuptools import setup, find_packages
import os
import re

# Read version from __init__.py
def get_version():
    init_path = os.path.join('src', 'docuforge', '__init__.py')
    with open(init_path, 'r') as f:
        version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name="docuforge",
    version=get_version(),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "reportlab>=3.6.0",
        "pillow>=9.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-benchmark>=4.0.0",
            "pytest-cov>=4.1.0",
            "pytest-lazy-fixture>=0.6.0",
            "hypothesis>=6.0.0",
            "pdf2image>=1.16.0",
            "imagehash>=4.3.0",
            "pypdf>=3.0.0",
            "flake8>=6.0.0",
        ],
        "weasyprint": [
            "weasyprint>=54.0",
        ],
    },
    python_requires=">=3.8",
    description="A flexible PDF document generation library",
    author="DocuForge Team",
)
