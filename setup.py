#!/usr/bin/env python
"""
Setup configuration for Trading AI System.

v79.1 Enhancements:
- Better dependency management
- Version sync with __version__.py
- Modern packaging practices
- Proper long description content type
- Better error handling
"""

from setuptools import setup, find_packages
from pathlib import Path
import re


def read_file(filename):
    """Read file safely."""
    filepath = Path(__file__).parent / filename
    if filepath.exists():
        with open(filepath, encoding="utf-8") as f:
            return f.read()
    return ""


def get_version():
    """Extract version from __version__.py."""
    try:
        version_file = Path(__file__).parent / "__version__.py"
        if version_file.exists():
            with open(version_file) as f:
                content = f.read()
                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return "0.79.1"


# Read long description
readme_content = read_file("README.md")

# Base dependencies
install_requires = [
    "numpy>=1.21.0",
    "pandas>=1.3.0",
    "lightgbm>=3.3.0",
    "scikit-learn>=1.0.0",
    "scipy>=1.7.0",
]

# Optional dependencies
extras_require = {
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-asyncio>=0.21.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
        "isort>=5.12.0",
        "pre-commit>=3.0.0",
    ],
    "docs": [
        "sphinx>=5.0.0",
        "sphinx-rtd-theme>=1.0.0",
        "sphinx-autodoc-typehints>=1.0.0",
    ],
    "live": [
        "requests>=2.28.0",
        "websockets>=10.0",
        "python-dotenv>=0.20.0",
        "aiohttp>=3.8.0",
    ],
    "analysis": [
        "matplotlib>=3.5.0",
        "seaborn>=0.12.0",
        "plotly>=5.0.0",
    ],
}

# Combine all optional dependencies
extras_require["all"] = sum(extras_require.values(), [])

setup(
    name="trading-ai-system",
    version=get_version(),
    author="Hamed Alinejad",
    author_email="hamedalinejad@example.com",
    maintainer="Hamed Alinejad",
    description="Production-grade algorithmic trading system with ML models",
    long_description=readme_content,
    long_description_content_type="text/markdown",
    url="https://github.com/hamedalinejad/trading_ai_system_refactored",
    project_urls={
        "Documentation": "https://trading-ai-system.readthedocs.io",
        "Source": "https://github.com/hamedalinejad/trading_ai_system_refactored",
        "Tracker": "https://github.com/hamedalinejad/trading_ai_system_refactored/issues",
        "Changelog": "https://github.com/hamedalinejad/trading_ai_system_refactored/releases",
    },
    license="MIT",
    packages=find_packages(include=["trading_ai_system", "trading_ai_system.*", "cli", "cli.*"]),
    package_data={
        "trading_ai_system": ["py.typed"],
    },
    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require=extras_require,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="trading algorithmic machine-learning quantitative finance automation",
    entry_points={
        "console_scripts": [
            "trading-ai=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    platforms="any",
)
