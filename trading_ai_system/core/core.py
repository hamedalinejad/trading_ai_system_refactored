"""
Core Module - Configuration, utilities, and infrastructure

Exports:
- Logger configuration
- Global state management
- System configuration
- Utility functions
- Type validators
"""

from trading_ai_system.core.core import (
    __version__,
    __author__,
    __license__,
    LoggerConfig,
    get_logger,
    GlobalState,
    LRUCache,
    hash_string,
    SystemConfig,
    PositionSizeMethod,
    ModelType,
    BrokerType,
    TimeframeType,
    get_timestamp_utc,
    timestamp_to_utc,
    is_utc_aware,
    DataFrameValidator,
    HealthCheck,
    load_json_config,
    ensure_path,
    get_file_hash,
    validate_mapping,
    validate_sequence,
    validate_mutable_mapping,
)

# Initialize module logger
logger = get_logger(__name__)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    
    # Logger
    "LoggerConfig",
    "get_logger",
    "logger",
    
    # Global state
    "GlobalState",
    "LRUCache",
    "hash_string",
    
    # Configuration
    "SystemConfig",
    "PositionSizeMethod",
    "ModelType",
    "BrokerType",
    "TimeframeType",
    
    # Utilities
    "get_timestamp_utc",
    "timestamp_to_utc",
    "is_utc_aware",
    "DataFrameValidator",
    "HealthCheck",
    "load_json_config",
    "ensure_path",
    "get_file_hash",
    "validate_mapping",
    "validate_sequence",
    "validate_mutable_mapping",
]

# Alias for compatibility
TradingSystemError = Exception
ConfigError = Exception
DataError = Exception
FeatureError = Exception
ModelError = Exception
ExecutionError = Exception
StrategyError = Exception
RiskError = Exception
LiveTradingError = Exception

# Configuration helpers
def get_global_config() -> dict:
    """Get global system configuration"""
    return {
        "version": __version__,
        "author": __author__,
        "timestamp": get_timestamp_utc(),
    }

def register_feature(*args, **kwargs) -> None:
    """Register feature for tracking (used by discovery)"""
    logger.debug(f"Feature registration: {args}")

__all__.extend([
    "TradingSystemError",
    "ConfigError",
    "DataError",
    "FeatureError",
    "ModelError",
    "ExecutionError",
    "StrategyError",
    "RiskError",
    "LiveTradingError",
    "get_global_config",
    "register_feature",
])
