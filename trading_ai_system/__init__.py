"""
Trading AI System - Production-grade algorithmic trading system with ML models

Main package initialization. Imports and exposes public API.
"""

from trading_ai_system.__version__ import (
    __version__,
    __author__,
    __description__,
)

# Import subpackages to make them available
from trading_ai_system import (
    core,
    data,
    features,
    models,
    strategy,
    risk,
    live,
    utils,
)

# Public API
__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "core",
    "data",
    "features",
    "models",
    "strategy",
    "risk",
    "live",
    "utils",
]
