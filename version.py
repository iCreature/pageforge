#!/usr/bin/env python
"""Version management utility for DocuForge."""

import re
import sys
import os
from datetime import datetime

def update_version(new_version):
    # Update __init__.py
    init_file = os.path.join('src', 'docuforge', '__init__.py')
    with open(init_file, 'r') as f:
        content = f.read()
    
    content = re.sub(
        r'^__version__ = ["\']([^"\']*)["\']',
        f'__version__ = "{new_version}"',
        content,
        flags=re.M
    )
    
    with open(init_file, 'w') as f:
        f.write(content)
    
    # Update CHANGELOG.md
    today = datetime.now().strftime('%Y-%m-%d')
    changelog_file = 'CHANGELOG.md'
    with open(changelog_file, 'r') as f:
        content = f.read()
    
    # Replace [Unreleased] section with the new version
    content = re.sub(
        r'## \[Unreleased\]',
        f'## [Unreleased]\n\n### Added\n\n### Changed\n\n### Fixed\n\n## [{new_version}] - {today}',
        content
    )
    
    # Add the new version to the link definitions
    content = re.sub(
        r'\[Unreleased\]: https://github\.com/yourorganization/docuforge/compare/v([^\.]+)\.([^\.]+)\.([^\.]+)\.\.\.HEAD',
        f'[Unreleased]: https://github.com/yourorganization/docuforge/compare/v{new_version}...HEAD\n[{new_version}]: https://github.com/yourorganization/docuforge/compare/v\\1.\\2.\\3...v{new_version}',
        content
    )
    
    with open(changelog_file, 'w') as f:
        f.write(content)
    
    # Git tag command guidance
    print(f"Files updated for version {new_version}")
    print("\nTo create a git tag for this release, run:")
    print(f"git add {init_file} {changelog_file}")
    print(f'git commit -m "Bump version to {new_version}"')
    print(f'git tag -a v{new_version} -m "Release version {new_version}"')
    print("git push && git push --tags")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python version.py NEW_VERSION")
        sys.exit(1)
    
    new_version = sys.argv[1]
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("Version must be in the format X.Y.Z")
        sys.exit(1)
    
    update_version(new_version)
