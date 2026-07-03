"""
Features Module - Technical indicators and feature engineering

Exports:
- Technical indicator calculators
- Feature engineering pipelines
- Pattern detection utilities
"""

from trading_ai_system.features.features import (
    FeatureMetadata,
    FeatureEngineeringError, FeatureRegistrationError,
    compute_rsi, compute_macd, compute_bollinger_bands,
    compute_atr, compute_stochastic,
    detect_engulfing, detect_doji, detect_inside_bar,
    detect_three_bar_patterns, detect_morning_evening_star,
    calculate_returns,
    engineer_features_for_timeframe,
)

__all__ = [
    "FeatureMetadata",
    "FeatureEngineeringError", "FeatureRegistrationError",
    "compute_rsi", "compute_macd", "compute_bollinger_bands",
    "compute_atr", "compute_stochastic",
    "detect_engulfing", "detect_doji", "detect_inside_bar",
    "detect_three_bar_patterns", "detect_morning_evening_star",
    "calculate_returns",
    "engineer_features_for_timeframe",
]
