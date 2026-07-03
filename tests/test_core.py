"""
Test suite for core.py bug fixes and improvements.
Run: pytest test_core_fixes.py -v
"""

import pytest
import sys
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Mock imports for testing
try:
    from trading_ai_system.core import core
except ImportError:
    # Use local core.py for testing
    import importlib.util
    spec = importlib.util.spec_from_file_location("core", "core.py")
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)


# ═══════════════════════════════════════════════════════════════════════════
# BUG FIX #1: from_dict() - Mutable Default Argument
# ═══════════════════════════════════════════════════════════════════════════

def test_config_from_dict_doesnt_modify_original():
    """Test that from_dict() doesn't modify the original dict."""
    original_dict = {
        'symbol': 'EURUSD',
        'market_type': 'spot',
        'base_timeframe': '1h'
    }
    original_copy = original_dict.copy()
    
    config = core.SystemConfig.from_dict(original_dict)
    
    # Original dict should be unchanged
    assert original_dict == original_copy
    # Config should be properly created
    assert config.symbol == 'EURUSD'
    assert config.market_type == core.MarketType.SPOT


# ═══════════════════════════════════════════════════════════════════════════
# BUG FIX #3 & #4: Thread-Safe GlobalState and Cache
# ═══════════════════════════════════════════════════════════════════════════

def test_global_state_thread_safe_creation():
    """Test that GlobalState is created safely in multi-threaded context."""
    states = []
    
    def get_state():
        state = core.get_global_state()
        states.append(id(state))
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(lambda _: get_state(), range(100))
    
    # All should be the same singleton instance
    assert len(set(states)) == 1


def test_cache_thread_safe_operations():
    """Test that cache operations are thread-safe."""
    state = core.get_global_state()
    results = []
    
    def set_and_get(i):
        state.set_cached(f"key_{i}", f"value_{i}")
        return state.get_cached(f"key_{i}")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(set_and_get, range(50)))
    
    # All operations should succeed
    assert len(results) == 50
    assert all(r is not None for r in results)


# ═══════════════════════════════════════════════════════════════════════════
# BUG FIX #5: Config Validation
# ═══════════════════════════════════════════════════════════════════════════

def test_invalid_config_rejected():
    """Test that invalid configurations are rejected."""
    # Test invalid commission
    invalid_config = core.SystemConfig(commission_per_side=2.0)
    valid, errors = invalid_config.validate()
    assert not valid
    assert any('commission' in e for e in errors)
    
    # Test invalid max_drawdown
    invalid_config = core.SystemConfig(max_drawdown=1.5)
    valid, errors = invalid_config.validate()
    assert not valid
    assert any('max_drawdown' in e for e in errors)
    
    # Test valid config
    valid_config = core.SystemConfig()
    valid, errors = valid_config.validate()
    assert valid
    assert len(errors) == 0


def test_set_config_validates():
    """Test that set_global_config() validates config."""
    state = core.get_global_state()
    
    # Should raise error for invalid config
    invalid_config = core.SystemConfig(commission_per_side=2.0)
    with pytest.raises(core.ConfigError):
        state.set_config(invalid_config)
    
    # Should accept valid config
    valid_config = core.SystemConfig(symbol="BTCUSD")
    state.set_config(valid_config)
    assert state.get_config().symbol == "BTCUSD"


# ═══════════════════════════════════════════════════════════════════════════
# BUG FIX #6: Feature Registry Thread-Safe
# ═══════════════════════════════════════════════════════════════════════════

def test_feature_registry_thread_safe():
    """Test that feature registry operations are thread-safe."""
    errors = []
    
    def register_and_get(i):
        try:
            core.register_feature(
                f"feature_{i}",
                category="technical",
                lookback=i + 1
            )
            registry = core.get_feature_registry()
            assert f"feature_{i}" in registry
        except Exception as e:
            errors.append(e)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(register_and_get, range(50))
    
    assert len(errors) == 0
    registry = core.get_feature_registry()
    assert len(registry) >= 50


def test_register_feature_validates_input():
    """Test that register_feature() validates input."""
    # Invalid feature name
    with pytest.raises(ValueError):
        core.register_feature("")
    
    with pytest.raises(ValueError):
        core.register_feature("   ")  # Whitespace only
    
    # Invalid lookback
    with pytest.raises(ValueError):
        core.register_feature("test", lookback=0)
    
    with pytest.raises(ValueError):
        core.register_feature("test", lookback=-1)
    
    # Valid registration
    core.register_feature("valid_feature", lookback=14)
    registry = core.get_feature_registry()
    assert "valid_feature" in registry


# ═══════════════════════════════════════════════════════════════════════════
# BUG FIX #8: JSON I/O Safety
# ═══════════════════════════════════════════════════════════════════════════

def test_json_config_encoding():
    """Test that JSON config uses proper encoding."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        
        # Save config
        data = {"symbol": "EURUSD", "test": "value"}
        core.save_json_config(data, str(config_path))
        
        # Verify file exists and contains valid JSON
        assert config_path.exists()
        
        # Load config
        loaded = core.load_json_config(str(config_path))
        assert loaded == data


def test_json_config_error_handling():
    """Test error handling in JSON operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test loading non-existent file
        result = core.load_json_config(str(Path(tmpdir) / "nonexistent.json"))
        assert result == {}
        
        # Test loading invalid JSON
        invalid_path = Path(tmpdir) / "invalid.json"
        invalid_path.write_text("{invalid json")
        
        with pytest.raises(core.ConfigError):
            core.load_json_config(str(invalid_path))


# ═══════════════════════════════════════════════════════════════════════════
# BUG FIX #9: get_request_config() Returns Copy
# ═══════════════════════════════════════════════════════════════════════════

def test_request_config_returns_copy():
    """Test that get_request_config() returns a copy."""
    config1 = {"key": "value"}
    core.set_request_config(config1)
    
    # Get config
    config2 = core.get_request_config()
    
    # Modify returned config
    config2["key"] = "modified"
    config2["new_key"] = "new_value"
    
    # Original in system should be unchanged
    config3 = core.get_request_config()
    assert config3["key"] == "value"
    assert "new_key" not in config3


# ═══════════════════════════════════════════════════════════════════════════
# BUG FIX #10 & #11: Registry and Health Return Copies
# ═══════════════════════════════════════════════════════════════════════════

def test_feature_registry_returns_copy():
    """Test that get_feature_registry() returns a copy."""
    core.register_feature("test_feature", category="test")
    
    registry1 = core.get_feature_registry()
    registry1["test_feature"]["category"] = "modified"
    registry1["fake_feature"] = {"data": "fake"}
    
    # Original should be unchanged
    registry2 = core.get_feature_registry()
    assert registry2["test_feature"]["category"] == "test"
    assert "fake_feature" not in registry2


def test_system_health_returns_copy():
    """Test that get_system_health() returns a copy."""
    core.update_system_health("degraded", details={"reason": "test"})
    
    health1 = core.get_system_health()
    health1.details["reason"] = "modified"
    health1.details["new_key"] = "new_value"
    
    # Original should be unchanged
    health2 = core.get_system_health()
    assert health2.details.get("reason") == "test"
    assert "new_key" not in health2.details


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE: SystemConfig.validate()
# ═══════════════════════════════════════════════════════════════════════════

def test_config_validate_method():
    """Test SystemConfig.validate() method."""
    # Valid config
    config = core.SystemConfig()
    valid, errors = config.validate()
    assert valid
    assert len(errors) == 0
    
    # Invalid: empty symbol
    config = core.SystemConfig(symbol="")
    valid, errors = config.validate()
    assert not valid
    assert any("symbol" in e for e in errors)
    
    # Invalid: test_size out of range
    config = core.SystemConfig(test_size=1.5)
    valid, errors = config.validate()
    assert not valid
    assert any("test_size" in e for e in errors)


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE: Timeframe Conversion Utils
# ═══════════════════════════════════════════════════════════════════════════

def test_timeframe_to_minutes():
    """Test timeframe_to_minutes() function."""
    assert core.timeframe_to_minutes("1m") == 1
    assert core.timeframe_to_minutes("5m") == 5
    assert core.timeframe_to_minutes("15m") == 15
    assert core.timeframe_to_minutes("1h") == 60
    assert core.timeframe_to_minutes("4h") == 240
    assert core.timeframe_to_minutes("1d") == 1440
    assert core.timeframe_to_minutes("1w") == 10080
    
    # Test with TimeFrame enum
    assert core.timeframe_to_minutes(core.TimeFrame.H1) == 60
    
    # Test invalid
    with pytest.raises(ValueError):
        core.timeframe_to_minutes("invalid")


def test_minutes_to_timeframe():
    """Test minutes_to_timeframe() function."""
    assert core.minutes_to_timeframe(1) == "1m"
    assert core.minutes_to_timeframe(5) == "5m"
    assert core.minutes_to_timeframe(60) == "1h"
    assert core.minutes_to_timeframe(240) == "4h"
    assert core.minutes_to_timeframe(1440) == "1d"
    
    # Test invalid
    with pytest.raises(ValueError):
        core.minutes_to_timeframe(0)
    
    with pytest.raises(ValueError):
        core.minutes_to_timeframe(999)


def test_timeframe_round_trip():
    """Test round-trip conversion between timeframes and minutes."""
    for tf in ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]:
        minutes = core.timeframe_to_minutes(tf)
        tf_back = core.minutes_to_timeframe(minutes)
        assert tf_back == tf


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE: Improved Data Validation
# ═══════════════════════════════════════════════════════════════════════════

def test_validate_dataframe_type_check():
    """Test that validate_dataframe() checks DataFrame type."""
    import pandas as pd
    
    # Test with None
    valid, errors = core.validate_dataframe(None)
    assert not valid
    assert any("None" in e for e in errors)
    
    # Test with non-DataFrame
    valid, errors = core.validate_dataframe([1, 2, 3])
    assert not valid
    assert any("not a pandas DataFrame" in e for e in errors)
    
    # Test with valid DataFrame
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    valid, errors = core.validate_dataframe(df)
    assert valid
    assert len(errors) == 0


def test_validate_dataframe_nan_check():
    """Test that validate_dataframe() checks for NaN values."""
    import pandas as pd
    import numpy as np
    
    # DataFrame with NaN in required column
    df = pd.DataFrame({
        "open": [1, 2, np.nan],
        "close": [2, 3, 4]
    })
    
    valid, errors = core.validate_dataframe(
        df,
        required_columns=["open", "close"]
    )
    assert not valid
    assert any("NaN" in e for e in errors)


# ═══════════════════════════════════════════════════════════════════════════
# QUALITY: Exception Classes
# ═══════════════════════════════════════════════════════════════════════════

def test_exception_hierarchy():
    """Test that all exception classes exist and inherit correctly."""
    exceptions = [
        core.StrategyError,
        core.RiskError,
        core.ConfigError,
        core.DataError,
        core.ModelError,
    ]
    
    for exc_class in exceptions:
        assert issubclass(exc_class, core.TradingSystemError)
        # Test instantiation
        exc = exc_class("test message")
        assert str(exc) == "test message"


# ═══════════════════════════════════════════════════════════════════════════
# QUALITY: hash_string() Algorithm Selection
# ═══════════════════════════════════════════════════════════════════════════

def test_hash_string_algorithms():
    """Test hash_string() with different algorithms."""
    test_str = "test_data"
    
    # SHA256 (default)
    hash1 = core.hash_string(test_str)
    assert len(hash1) == 16
    
    hash2 = core.hash_string(test_str, algorithm="sha256")
    assert hash1 == hash2
    
    # MD5
    hash3 = core.hash_string(test_str, algorithm="md5")
    assert len(hash3) == 16
    assert hash3 != hash1  # Different algorithms
    
    # Invalid algorithm
    with pytest.raises(ValueError):
        core.hash_string(test_str, algorithm="invalid")


# ═══════════════════════════════════════════════════════════════════════════
# QUALITY: Error Handling in System Lifecycle
# ═══════════════════════════════════════════════════════════════════════════

def test_initialize_system_error_handling():
    """Test that initialize_system() handles errors properly."""
    # Valid config should work
    config = core.SystemConfig(symbol="TEST")
    core.initialize_system(config)
    assert core.get_global_config().symbol == "TEST"
    
    # Invalid config should raise error
    invalid_config = core.SystemConfig(commission_per_side=2.0)
    with pytest.raises(core.ConfigError):
        core.initialize_system(invalid_config)


def test_shutdown_system():
    """Test system shutdown."""
    core.initialize_system()
    core.set_request_config({"test": "data"})
    
    core.shutdown_system()
    
    # Request config should be cleared
    config = core.get_request_config()
    assert config == {}


# ═══════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
