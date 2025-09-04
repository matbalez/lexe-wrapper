#!/usr/bin/env python3
"""
Setup script for lexe-wrapper package
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define requirements directly
requirements = ["requests>=2.31.0"]

setup(
    name="lexe-wrapper",
    version="1.2.1",
    author="Mat Balez",
    author_email="matbalez@gmail.com",
    description="Unofficial, open-source Python wrapper for Lexe Bitcoin Lightning Network wallet integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lexe-app/lexe-wrapper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "flake8",
        ],
    },
    entry_points={
        "console_scripts": [
            "lexe-wrapper=lexe_wrapper.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="bitcoin lightning network lexe wallet cryptocurrency unofficial open-source wrapper",
    project_urls={
        "Bug Reports": "https://github.com/lexe-app/lexe-wrapper/issues",
        "Source": "https://github.com/lexe-app/lexe-wrapper",
        "Documentation": "https://github.com/lexe-app/lexe-wrapper#readme",
    },
)