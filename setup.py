#!/usr/bin/env python
"""
Setup configuration for Trading AI System.
Modern projects should use pyproject.toml, but this is provided for compatibility.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from __version__.py
version_file = Path(__file__).parent / "trading_ai_system" / "__version__.py"
version = {}
if version_file.exists():
    with open(version_file) as f:
        for line in f:
            if line.startswith('__version__'):
                exec(line, version)
                break

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, encoding="utf-8") as f:
        long_description = f.read()

# Base dependencies
install_requires = [
    "numpy>=1.21.0",
    "pandas>=1.3.0",
    "lightgbm>=3.3.0",
    "scikit-learn>=1.0.0",
]

# Optional dependencies
extras_require = {
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
        "isort>=5.12.0",
        "pre-commit>=3.0.0",
    ],
    "docs": [
        "sphinx>=5.0.0",
        "sphinx-rtd-theme>=1.0.0",
    ],
    "live": [
        "requests>=2.28.0",
        "websockets>=10.0",
        "python-dotenv>=0.20.0",
    ],
}

setup(
    name="trading-ai-system",
    version=version.get("__version__", "0.79.0"),
    author="Trading AI System",
    description="Production-grade algorithmic trading system with ML models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trading-ai-system",
    license="MIT",
    packages=find_packages(include=["trading_ai_system", "trading_ai_system.*"]),
    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require=extras_require,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    keywords="trading algorithmic machine-learning quantitative",
    project_urls={
        "Documentation": "https://trading-ai-system.readthedocs.io",
        "Source": "https://github.com/yourusername/trading-ai-system",
        "Tracker": "https://github.com/yourusername/trading-ai-system/issues",
    },
    include_package_data=True,
    zip_safe=False,
)
