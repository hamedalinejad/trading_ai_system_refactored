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
        'base_timeframe': '1h'
    }
    original_copy = original_dict.copy()
    
    config = core.SystemConfig.from_dict(original_dict)
    
    # Original dict should be unchanged
    assert original_dict == original_copy
    # Config should be properly created
    assert config.symbol == 'EURUSD'
    assert config.base_timeframe == '1h'


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
            # Use the feature_registry function with register=True
            core.feature_registry(
                f"feature_{i}",
                register=True,
                value={'category': 'technical', 'lookback': i + 1}
            )
            registry = core.feature_registry()  # Get entire registry
            assert f"feature_{i}" in registry
        except Exception as e:
            errors.append(e)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(register_and_get, range(50))
    
    assert len(errors) == 0
    registry = core.feature_registry()
    assert len(registry) >= 50


def test_register_feature_validates_input():
    """Test that feature_registry() validates input."""
    # Valid registration
    core.feature_registry("valid_feature", register=True, value={'lookback': 14})
    registry = core.feature_registry()
    assert "valid_feature" in registry
    assert registry["valid_feature"]['lookback'] == 14


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
    """Test that feature_registry() returns a copy."""
    # Test that modifying returned dict doesn't affect subsequent calls
    core.feature_registry("test_feature", register=True, value={"data": "original"})
    
    # Get registry and clear it locally (don't affect stored one)
    registry1 = core.feature_registry()
    registry1["fake_feature"] = {"data": "should_not_persist"}
    
    # Check that fake_feature was not added to actual registry
    registry2 = core.feature_registry()
    assert "fake_feature" not in registry2
    assert "test_feature" in registry2


def test_system_health_returns_copy():
    """Test that system_health() returns a copy."""
    health1 = core.system_health()
    health1["test_key"] = "test_value"
    health1["modified"] = True
    
    # Original should be unchanged (copy should not affect stored data)
    health2 = core.system_health()
    assert "test_key" not in health2
    assert health2.get("modified") is None
    
    # Both should be valid health dicts
    assert "status" in health1
    assert "status" in health2


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
    assert core.timeframe_to_minutes("1M") == 1
    assert core.timeframe_to_minutes("5M") == 5
    assert core.timeframe_to_minutes("15M") == 15
    assert core.timeframe_to_minutes("1H") == 60
    assert core.timeframe_to_minutes("4H") == 240
    assert core.timeframe_to_minutes("1D") == 1440
    assert core.timeframe_to_minutes("1W") == 10080
    
    # Test invalid
    with pytest.raises(ValueError):
        core.timeframe_to_minutes("invalid")
    
    with pytest.raises(ValueError):
        core.timeframe_to_minutes("1X")


def test_minutes_to_timeframe():
    """Test minutes_to_timeframe() function."""
    assert core.minutes_to_timeframe(1) == "1M"
    assert core.minutes_to_timeframe(5) == "5M"
    assert core.minutes_to_timeframe(60) == "1H"
    assert core.minutes_to_timeframe(240) == "4H"
    assert core.minutes_to_timeframe(1440) == "1D"
    assert core.minutes_to_timeframe(10080) == "1W"
    
    # Test invalid
    with pytest.raises(ValueError):
        core.minutes_to_timeframe(0)
    
    with pytest.raises(ValueError):
        core.minutes_to_timeframe(-10)


def test_timeframe_round_trip():
    """Test round-trip conversion between timeframes and minutes."""
    for tf in ["1M", "5M", "15M", "1H", "4H", "1D", "1W"]:
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
    assert any("dict" in e or "DataFrame" in e for e in errors)
    
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
    
    valid, errors = core.validate_dataframe(df)
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
    
    # SHA256 (default) - 64 hex characters = 32 bytes
    hash1 = core.hash_string(test_str)
    assert len(hash1) == 64  # SHA256 produces 64 hex characters
    
    hash2 = core.hash_string(test_str, algorithm="sha256")
    assert hash1 == hash2
    
    # MD5 - 32 hex characters = 16 bytes
    hash3 = core.hash_string(test_str, algorithm="md5")
    assert len(hash3) == 32  # MD5 produces 32 hex characters
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
