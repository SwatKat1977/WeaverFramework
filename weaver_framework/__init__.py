"""
Copyright 2026 Weaver Framework Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Version information for Weaver Framework.

__all__ = ["__version__", "VERSION"]

# Semantic version components
MAJOR = 0
MINOR = 2
PATCH = 0

# Pre-release tag using PEP 440 standard or None if not required:
# Type              Format Example
# Alpha             0.1.0a1
# Beta              0.1.0b1
# Release candidate 0.1.0rc1
PRE_RELEASE = None


def build_version_string(major: int,
                         minor: int,
                         patch: int,
                         prerelease: str | None = None) -> str:
    """Build a PEP 440-compatible version string."""

    version = f"{major}.{minor}.{patch}"

    if prerelease:
        version += prerelease

    return version


# Version tuple for comparisons
VERSION = (MAJOR, MINOR, PATCH, PRE_RELEASE or "")

# Construct the string representation
__version__ = build_version_string(MAJOR, MINOR, PATCH, PRE_RELEASE)
