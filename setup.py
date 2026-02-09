#!/usr/bin/env python
"""
Setup script for PyKIS package.
This file is kept for backward compatibility and editable installs.
Configuration is primarily handled through pyproject.toml.
"""

from setuptools import find_packages, setup

# Minimal setup.py for compatibility with pip install -e .
# All configuration is in pyproject.toml
if __name__ == "__main__":
    setup(
        packages=find_packages(where=".", include=["pykis", "pykis.*"]),
        package_dir={"": "."},
    )
