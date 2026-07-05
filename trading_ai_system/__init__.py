"""
Trading AI System - Production-grade algorithmic trading system with ML models

Main package initialization with public API exposure.
Supports:
- Machine learning model training and inference
- Live trading execution and monitoring
- Risk management and position sizing
- Strategy development and backtesting
- Data fetching and feature engineering
- Automated indicator discovery and analysis

v79.2 - Enhanced with indicator discovery and feature importance analysis
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Version info
from trading_ai_system.__version__ import (
    __version__,
    __author__,
    __description__,
)

# Core utilities
from trading_ai_system.core import (
    TradingSystemError,
    get_global_config,
)

# Import subpackages - lazy load to avoid dependency issues
try:
    from trading_ai_system import core
except ImportError as e:
    logger.warning(f"Failed to import core module: {e}")
    core = None

try:
    from trading_ai_system import data
except ImportError as e:
    logger.warning(f"Failed to import data module: {e}")
    data = None

try:
    from trading_ai_system import features
except ImportError as e:
    logger.warning(f"Failed to import features module: {e}")
    features = None

try:
    from trading_ai_system import models
except ImportError as e:
    logger.warning(f"Failed to import models module: {e}")
    models = None

try:
    from trading_ai_system import discovery
except ImportError as e:
    logger.warning(f"Failed to import discovery module: {e}")
    discovery = None

try:
    from trading_ai_system import strategy
except ImportError as e:
    logger.warning(f"Failed to import strategy module: {e}")
    strategy = None

try:
    from trading_ai_system import risk
except ImportError as e:
    logger.warning(f"Failed to import risk module: {e}")
    risk = None

try:
    from trading_ai_system import live
except ImportError as e:
    logger.warning(f"Failed to import live module: {e}")
    live = None

try:
    from trading_ai_system import utils
except ImportError as e:
    logger.warning(f"Failed to import utils module: {e}")
    utils = None


def get_system_info() -> dict:
    """Get system information and configuration.
    
    Returns:
        dict: System info including version, config, and module status
    """
    try:
        config = get_global_config()
    except:
        config = {}
    
    modules_status = {
        "core": core is not None,
        "data": data is not None,
        "features": features is not None,
        "models": models is not None,
        "discovery": discovery is not None,
        "strategy": strategy is not None,
        "risk": risk is not None,
        "live": live is not None,
        "utils": utils is not None,
    }
    
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "python_version": sys.version,
        "modules": modules_status,
        "config": config,
    }


# Public API
__all__ = [
    # Version & metadata
    "__version__",
    "__author__",
    "__description__",
    
    # Subpackages
    "core",
    "data",
    "features",
    "models",
    "discovery",
    "strategy",
    "risk",
    "live",
    "utils",
    
    # Core exports
    "TradingSystemError",
    "get_global_config",
    
    # Functions
    "get_system_info",
]


# Initialize logging
logger.info(f"Trading AI System v{__version__} initialized")
logger.debug(f"Author: {__author__}")
logger.debug(f"Description: {__description__}")

# Verify module imports
missing_modules = [name for name, loaded in {
    "core": core,
    "data": data,
    "features": features,
    "models": models,
    "discovery": discovery,
    "strategy": strategy,
    "risk": risk,
    "live": live,
    "utils": utils,
}.items() if loaded is None]

if missing_modules:
    logger.warning(f"Some modules failed to import: {missing_modules}")
else:
    logger.info("All modules loaded successfully")
