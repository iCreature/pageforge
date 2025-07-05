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
    author="Mxolisi Msweli",
    author_email="mxolisi.msweli@example.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: Office/Business",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Text Processing :: Markup",
    ],
    url="https://github.com/mxolisi-msweli/docuforge",
)
