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

v79.4 - Enhanced module loading, discovery integration, caching, persistence
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

try:
    from trading_ai_system.__version__ import (
        __version__,
        __author__,
        __description__,
    )
except ImportError:
    __version__ = "0.79.4"
    __author__ = "Hamed Alinejad"
    __description__ = "Trading AI System with ML and Discovery"

try:
    from trading_ai_system.core import (
        TradingSystemError,
        get_global_config,
        register_feature,
        get_logger,
    )
except ImportError as e:
    logger.error(f"Critical: Failed to import core module: {e}")
    TradingSystemError = Exception
    def get_global_config():
        return {}
    def register_feature(*args, **kwargs):
        pass
    def get_logger(name):
        return logging.getLogger(name)


class ModuleLoader:
    """Lazy load submodules with error handling"""
    
    def __init__(self):
        self._modules: Dict[str, Optional[Any]] = {}
        self._errors: Dict[str, str] = {}
        self._load_all()
    
    def _load_all(self) -> None:
        """Load all submodules"""
        module_names = ['core', 'data', 'features', 'models', 'discovery', 'strategy', 'risk', 'live', 'utils']
        
        for module_name in module_names:
            try:
                self._modules[module_name] = __import__(f'trading_ai_system.{module_name}', fromlist=[module_name])
                logger.debug(f"Loaded module: {module_name}")
            except ImportError as e:
                self._modules[module_name] = None
                self._errors[module_name] = str(e)
                logger.warning(f"Failed to import {module_name}: {e}")
            except Exception as e:
                self._modules[module_name] = None
                self._errors[module_name] = str(e)
                logger.error(f"Error loading {module_name}: {e}")
    
    def get(self, module_name: str) -> Optional[Any]:
        """Get loaded module"""
        return self._modules.get(module_name)
    
    def get_status(self) -> Dict[str, bool]:
        """Get module loading status"""
        return {name: mod is not None for name, mod in self._modules.items()}
    
    def get_errors(self) -> Dict[str, str]:
        """Get module loading errors"""
        return self._errors.copy()


_loader = ModuleLoader()

core = _loader.get('core')
data = _loader.get('data')
features = _loader.get('features')
models = _loader.get('models')
discovery = _loader.get('discovery')
strategy = _loader.get('strategy')
risk = _loader.get('risk')
live = _loader.get('live')
utils = _loader.get('utils')


def get_system_info() -> Dict[str, Any]:
    """Get system information and configuration"""
    try:
        config = get_global_config()
    except Exception:
        config = {}
    
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "python_version": sys.version,
        "modules": _loader.get_status(),
        "config": config,
    }


def get_module_errors() -> Dict[str, str]:
    """Get module loading errors"""
    return _loader.get_errors()


def verify_modules(required: Optional[list] = None) -> bool:
    """
    Verify required modules are loaded.
    
    Args:
        required: List of required module names. If None, checks all.
        
    Returns:
        True if all required modules loaded, False otherwise
    """
    status = _loader.get_status()
    
    if required is None:
        required = list(status.keys())
    
    missing = [m for m in required if not status.get(m, False)]
    
    if missing:
        logger.error(f"Missing required modules: {missing}")
        return False
    
    return True


def initialize_system(
    enable_discovery: bool = True,
    enable_caching: bool = True,
    enable_logging: bool = True
) -> bool:
    """
    Initialize trading system with options.
    
    Args:
        enable_discovery: Enable indicator discovery module
        enable_caching: Enable feature caching
        enable_logging: Enable system logging
        
    Returns:
        True if initialization successful
    """
    try:
        if enable_logging:
            logger.info(f"Initializing Trading AI System v{__version__}")
        
        status = _loader.get_status()
        
        if enable_discovery and not status.get('discovery'):
            logger.warning("Discovery module not available")
        
        if enable_caching and features:
            try:
                features.feature_cache.enable_caching = True
                if enable_logging:
                    logger.info("Feature caching enabled")
            except AttributeError:
                logger.warning("Feature cache not available")
        
        if enable_logging:
            logger.info(f"System initialized: {sum(status.values())}/{len(status)} modules loaded")
        
        return all(status.values())
    
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return False


def get_pipeline() -> Dict[str, Any]:
    """Get standard pipeline configuration"""
    return {
        "data_loader": data,
        "feature_engineer": features,
        "discovery": discovery,
        "model": models,
        "strategy": strategy,
        "risk_manager": risk,
        "live_trader": live,
    }


__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "core",
    "data",
    "features",
    "models",
    "discovery",
    "strategy",
    "risk",
    "live",
    "utils",
    "TradingSystemError",
    "get_global_config",
    "register_feature",
    "get_logger",
    "get_system_info",
    "get_module_errors",
    "verify_modules",
    "initialize_system",
    "get_pipeline",
]

logger.info(f"Trading AI System v{__version__} loaded")
status = _loader.get_status()
loaded_count = sum(status.values())
total_count = len(status)
logger.info(f"Modules: {loaded_count}/{total_count} loaded successfully")

if loaded_count < total_count:
    errors = _loader.get_errors()
    for module, error in errors.items():
        logger.debug(f"{module}: {error}")
