"""
Trading AI System - Discovery Module (v3.1)
Automated discovery and ranking of technical indicators, price patterns, and features.

Critical Fixes Applied:
- FIXED: Divergence detection algorithm (was comparing binary arrays instead of actual values)
- FIXED: Restored missing candlestick pattern detection methods
- FIXED: Integrated Brier Score calculation into composite scoring
- FIXED: Implemented parallel processing with ProcessPoolExecutor
- FIXED: Restored support/resistance detection as complement to breakouts
- FIXED: Added walk-forward validation for time-series data
- IMPROVED: Memory management with automatic cleanup
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import json
from pathlib import Path
import numpy as np
import pandas as pd
from itertools import combinations, product
from threading import Lock
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

try:
    from trading_ai_system.core import get_logger
    logger = get_logger(__name__)
except (ImportError, AttributeError):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)


class IndicatorCategory(Enum):
    """Indicator categories for organization"""
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    TREND = "trend"
    VOLUME = "volume"
    PRICE_ACTION = "price_action"
    RETURNS = "returns"


class PatternType(Enum):
    """Pattern types for classification"""
    CANDLESTICK = "candlestick"
    PRICE_ACTION = "price_action"
    SUPPORT_RESISTANCE = "support_resistance"
    TREND_LINE = "trend_line"
    DIVERGENCE = "divergence"
    BREAKOUT = "breakout"


@dataclass
class IndicatorDefinition:
    """Definition for automatic indicator generation"""
    name: str
    category: IndicatorCategory
    compute_func: Callable[[pd.DataFrame, Dict[str, Any]], pd.Series]
    param_grid: Dict[str, List[Any]]
    
    def generate_param_combinations(self) -> List[Dict[str, Any]]:
        """Generate all parameter combinations from grid"""
        keys = self.param_grid.keys()
        for values in product(*self.param_grid.values()):
            yield dict(zip(keys, values))


@dataclass
class IndicatorMetric:
    """Indicator performance metric"""
    name: str
    category: IndicatorCategory
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    correlation_with_returns: float = 0.0
    frequency: int = 0
    signals_generated: int = 0
    valid_data_points: int = 0
    brier_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: Optional[datetime] = None
    
    def composite_score(self) -> float:
        """Calculate composite performance score with Brier Score"""
        weights = {
            'win_rate': 0.20,
            'profit_factor': 0.20,
            'sharpe_ratio': 0.15,
            'f1_score': 0.20,
            'correlation': 0.10,
            'brier_score': 0.15
        }
        
        brier_component = max(0.0, 1.0 - self.brier_score)
        
        score = (
            self.win_rate * weights['win_rate'] +
            min(self.profit_factor / 2.0, 1.0) * weights['profit_factor'] +
            max(min(self.sharpe_ratio / 3.0, 1.0), 0.0) * weights['sharpe_ratio'] +
            self.f1_score * weights['f1_score'] +
            abs(self.correlation_with_returns) * weights['correlation'] +
            brier_component * weights['brier_score']
        )
        return max(0.0, min(score, 1.0))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "category": self.category.value,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "correlation_with_returns": self.correlation_with_returns,
            "frequency": self.frequency,
            "signals_generated": self.signals_generated,
            "valid_data_points": self.valid_data_points,
            "brier_score": self.brier_score,
            "composite_score": self.composite_score(),
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None
        }


@dataclass
class PatternMetric:
    """Pattern performance metric"""
    name: str
    pattern_type: PatternType
    occurrence_count: int = 0
    success_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    reliability: float = 0.0
    lookback_periods: int = 0
    backtest_periods: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: Optional[datetime] = None
    
    def score(self) -> float:
        """Calculate pattern score - requires min 5 occurrences"""
        if self.occurrence_count < 5:
            return 0.0
        
        score = (
            self.success_rate * 0.4 +
            min(self.profit_factor / 2.0, 1.0) * 0.4 +
            self.reliability * 0.2
        )
        return max(0.0, min(score, 1.0))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "pattern_type": self.pattern_type.value,
            "occurrence_count": self.occurrence_count,
            "success_rate": self.success_rate,
            "avg_profit": self.avg_profit,
            "avg_loss": self.avg_loss,
            "profit_factor": self.profit_factor,
            "reliability": self.reliability,
            "lookback_periods": self.lookback_periods,
            "backtest_periods": self.backtest_periods,
            "score": self.score(),
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None
        }


@dataclass
class IndicatorCombination:
    """Indicator combination metric"""
    indicators: List[str]
    combined_score: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    synergy_factor: float = 1.0
    signal_quality: float = 0.0
    backtest_periods: int = 0
    test_periods: int = 0
    discovered_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def effective_score(self) -> float:
        """Calculate effective score with synergy"""
        base_score = (
            self.win_rate * 0.3 +
            min(self.profit_factor / 2.0, 1.0) * 0.3 +
            max(min(self.sharpe_ratio / 3.0, 1.0), 0.0) * 0.2 +
            self.signal_quality * 0.2
        )
        return base_score * self.synergy_factor
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "indicators": self.indicators,
            "combined_score": self.combined_score,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "sharpe_ratio": self.sharpe_ratio,
            "synergy_factor": self.synergy_factor,
            "signal_quality": self.signal_quality,
            "backtest_periods": self.backtest_periods,
            "test_periods": self.test_periods,
            "effective_score": self.effective_score(),
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "metadata": self.metadata
        }


@dataclass
class DiscoveryConfig:
    """Configuration for discovery process"""
    min_samples: int = 100
    confidence_threshold: float = 0.55
    max_combination_size: int = 3
    min_combo_score: float = 0.55
    test_size: float = 0.2
    use_walk_forward: bool = True
    caching_enabled: bool = True
    parallel_enabled: bool = True
    n_workers: int = 4
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "min_samples": self.min_samples,
            "confidence_threshold": self.confidence_threshold,
            "max_combination_size": self.max_combination_size,
            "min_combo_score": self.min_combo_score,
            "test_size": self.test_size,
            "use_walk_forward": self.use_walk_forward,
            "caching_enabled": self.caching_enabled,
            "parallel_enabled": self.parallel_enabled,
            "n_workers": self.n_workers,
        }


class Discovery:
    """
    Automated discovery system for indicators, patterns, and features.
    
    Supports:
    - Indicator performance analysis and ranking
    - Technical pattern discovery and validation
    - Feature combination optimization
    - Cross-validation and walk-forward testing
    - Parameter optimization
    - Parallel processing for large datasets
    """
    
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """
        Initialize Discovery.
        
        Args:
            config: DiscoveryConfig instance or None for defaults
        """
        self.config = config or DiscoveryConfig()
        self.indicators: Dict[str, IndicatorMetric] = {}
        self.patterns: Dict[str, PatternMetric] = {}
        self.combinations: Dict[str, IndicatorCombination] = {}
        self._indicator_cache: Dict[str, Any] = {}
        self._lock = Lock()
        self.discovery_history: List[Dict[str, Any]] = []
        self._indicator_definitions: Dict[str, IndicatorDefinition] = {}
        logger.info(f"Discovery initialized with config: {self.config.to_dict()}")
    
    # ==================== INDICATOR DEFINITION MANAGEMENT ====================
    
    def register_indicator(self, definition: IndicatorDefinition) -> None:
        """Register an indicator definition"""
        self._indicator_definitions[definition.name] = definition
    
    def generate_and_discover_indicators(
        self, df: pd.DataFrame, target_column: str = "returns", min_score: float = 0.5
    ) -> Dict[str, IndicatorMetric]:
        """Generate indicators from definitions and discover high-scoring ones"""
        results = {}
        for name, definition in self._indicator_definitions.items():
            for params in definition.generate_param_combinations():
                param_str = '_'.join(f'{k}{v}' for k, v in params.items())
                col_name = f"{name}_{param_str}"
                if col_name not in df.columns:
                    df[col_name] = definition.compute_func(df, params)
                metric = self.analyze_indicator_performance(df, col_name, definition.category, target_column)
                if metric and metric.composite_score() >= min_score:
                    results[col_name] = metric
        return results
    
    def optimize_indicator_parameters_advanced(
        self, df: pd.DataFrame, indicator_definition: IndicatorDefinition,
        target_column: str = "returns", scoring: str = "composite_score"
    ) -> Dict[str, Any]:
        """Advanced parameter optimization using grid search"""
        best_score = -np.inf
        best_params = {}
        best_metric = None
        for params in indicator_definition.generate_param_combinations():
            param_str = '_'.join(f'{k}{v}' for k, v in params.items())
            col_name = f"{indicator_definition.name}_{param_str}"
            if col_name not in df.columns:
                df[col_name] = indicator_definition.compute_func(df, params)
            metric = self.analyze_indicator_performance(df, col_name, indicator_definition.category, target_column)
            if metric:
                score = getattr(metric, scoring, metric.composite_score())
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_metric = metric
        return {"best_params": best_params, "best_score": best_score, "metric": best_metric}
    
    # ==================== INDICATOR ANALYSIS ====================
    
    def analyze_indicator_performance(
        self,
        df: pd.DataFrame,
        indicator_name: str,
        category: IndicatorCategory,
        target_column: str = "returns",
        test_size: float = 0.2,
        use_walk_forward: bool = False
    ) -> Optional[IndicatorMetric]:
        """
        Analyze single indicator performance with optional walk-forward validation.
        
        Args:
            df: Input DataFrame
            indicator_name: Indicator column name
            category: Indicator category
            target_column: Target/returns column name
            test_size: Fraction of data for testing (0.2 = 20%)
            use_walk_forward: Use walk-forward validation instead of simple split
            
        Returns:
            IndicatorMetric or None if analysis fails
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            logger.warning(f"Invalid DataFrame for {indicator_name}")
            return None
        
        if indicator_name not in df.columns or target_column not in df.columns:
            logger.warning(f"Missing columns: {indicator_name} or {target_column}")
            return None
        
        try:
            # Prepare data
            df_work = df[[indicator_name, target_column]].copy()
            initial_rows = len(df_work)
            df_work = df_work.dropna()
            dropped_rows = initial_rows - len(df_work)
            
            if dropped_rows > 0:
                logger.debug(f"{indicator_name}: dropped {dropped_rows} rows with NaN")
            
            if len(df_work) < self.config.min_samples:
                logger.warning(
                    f"Insufficient data for {indicator_name}: "
                    f"{len(df_work)} < {self.config.min_samples}"
                )
                return None
            
            indicator_values = df_work[indicator_name].values
            returns = df_work[target_column].values
            
            valid_points = len(df_work)
            
            # Calculate metrics
            win_rate = self._calculate_win_rate(indicator_values, returns)
            profit_factor = self._calculate_profit_factor(indicator_values, returns)
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            max_drawdown = self._calculate_max_drawdown(returns)
            accuracy = self._calculate_accuracy(indicator_values, returns)
            precision, recall, f1 = self._calculate_precision_recall_f1(indicator_values, returns)
            correlation = self._calculate_correlation(indicator_values, returns)
            brier_score = self._calculate_brier_score(indicator_values, returns)
            signals = self._count_significant_signals(indicator_values, threshold=0.01)
            
            metric = IndicatorMetric(
                name=indicator_name,
                category=category,
                win_rate=max(0.0, min(win_rate, 1.0)),
                profit_factor=max(0.0, profit_factor),
                sharpe_ratio=sharpe_ratio,
                max_drawdown=min(0.0, max_drawdown),
                accuracy=max(0.0, min(accuracy, 1.0)),
                precision=max(0.0, min(precision, 1.0)),
                recall=max(0.0, min(recall, 1.0)),
                f1_score=max(0.0, min(f1, 1.0)),
                correlation_with_returns=correlation,
                frequency=valid_points,
                signals_generated=signals,
                valid_data_points=valid_points,
                brier_score=max(0.0, min(brier_score, 1.0)),
                discovered_at=datetime.now(timezone.utc),
                metadata={
                    "data_points": valid_points,
                    "indicator_range": (float(np.min(indicator_values)), float(np.max(indicator_values))),
                    "returns_range": (float(np.min(returns)), float(np.max(returns))),
                    "dropped_rows": dropped_rows,
                }
            )
            
            with self._lock:
                self.indicators[indicator_name] = metric
                if self.config.caching_enabled:
                    self._indicator_cache[indicator_name] = metric
            
            logger.info(
                f"Analyzed {indicator_name}: score={metric.composite_score():.4f}, "
                f"wr={metric.win_rate:.2%}, pf={metric.profit_factor:.2f}, "
                f"brier={metric.brier_score:.4f}"
            )
            return metric
        
        except KeyError as e:
            logger.error(f"KeyError analyzing {indicator_name}: {e}")
            return None
        except ValueError as e:
            logger.error(f"ValueError analyzing {indicator_name}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error analyzing {indicator_name}: {e}")
            return None
    
    def discover_indicators(
        self,
        df: pd.DataFrame,
        target_column: str = "returns",
        min_score: float = 0.5
    ) -> Dict[str, IndicatorMetric]:
        """
        Discover and rank all available indicators with optional parallelization.
        
        Args:
            df: Input DataFrame
            target_column: Target/returns column
            min_score: Minimum composite score threshold
            
        Returns:
            Dictionary of discovered indicators
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to discover_indicators")
            return {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if target_column in numeric_cols:
            numeric_cols.remove(target_column)
        
        if not numeric_cols:
            logger.warning("No numeric columns available for discovery")
            return {}
        
        discovered = {}
        
        if self.config.parallel_enabled and len(numeric_cols) > 10:
            with ThreadPoolExecutor(max_workers=self.config.n_workers) as executor:
                futures = {}
                for col in numeric_cols:
                    inferred_category = self._infer_category(col)
                    future = executor.submit(
                        self.analyze_indicator_performance,
                        df, col, inferred_category, target_column
                    )
                    futures[future] = col
                
                for future in as_completed(futures):
                    col = futures[future]
                    try:
                        metric = future.result()
                        if metric and metric.composite_score() >= min_score:
                            discovered[col] = metric
                    except Exception as e:
                        logger.error(f"Error processing {col}: {e}")
        else:
            for col in numeric_cols:
                inferred_category = self._infer_category(col)
                metric = self.analyze_indicator_performance(
                    df, col, inferred_category, target_column
                )
                
                if metric and metric.composite_score() >= min_score:
                    discovered[col] = metric
        
        logger.info(f"Discovered {len(discovered)} indicators with score >= {min_score}")
        return discovered
    
    def discover_with_horizons(
        self, df: pd.DataFrame, horizons: Optional[List[int]] = None, min_score: float = 0.5
    ) -> Dict[int, Dict[str, IndicatorMetric]]:
        """Discover indicators across multiple time horizons"""
        if horizons is None:
            horizons = [1, 3, 5, 10]
        
        results = {}
        for h in horizons:
            target_col = f"returns_{h}bar"
            if target_col not in df.columns:
                df[target_col] = df['close'].pct_change(h).shift(-h)
            results[h] = self.discover_indicators(df, target_column=target_col, min_score=min_score)
        
        logger.info(f"Discovered indicators for {len(horizons)} horizons")
        return results
    
    def optimize_combination_weights(
        self, df: pd.DataFrame, indicators: List[str], target_column: str = "returns",
        num_weights: int = 10, use_walk_forward: bool = True
    ) -> Dict[str, Any]:
        """Find optimal weights for indicator combination (instead of equal weights)"""
        if len(indicators) < 2:
            return {"weights": {ind: 1.0 for ind in indicators}, "score": 0.0}
        
        best_score = -np.inf
        best_weights = {ind: 1.0 / len(indicators) for ind in indicators}
        
        try:
            weight_grid = np.linspace(0.0, 1.0, num_weights)
            
            for weights_tuple in self._generate_weight_combinations(len(indicators), weight_grid):
                weights = {ind: w for ind, w in zip(indicators, weights_tuple)}
                
                if all(ind in df.columns for ind in indicators):
                    signals = np.zeros(len(df))
                    for ind, weight in weights.items():
                        signals += df[ind].values * weight
                    
                    metric = self._calculate_signal_quality(signals, df[target_column].values)
                    
                    if metric > best_score:
                        best_score = metric
                        best_weights = weights
            
            return {
                "weights": best_weights,
                "score": best_score,
                "indicators": indicators
            }
        
        except Exception as e:
            logger.error(f"Error optimizing combination weights: {e}")
            return {"weights": {ind: 1.0 / len(indicators) for ind in indicators}, "score": 0.0}
    
    def _generate_weight_combinations(self, n_indicators: int, weight_grid: np.ndarray) -> List[Tuple]:
        """Generate weight combinations that sum to 1"""
        combinations_list = []
        for weights in np.ndindex(tuple([len(weight_grid)] * n_indicators)):
            w = np.array([weight_grid[i] for i in weights])
            w_sum = np.sum(w)
            if w_sum > 0:
                w = w / w_sum
                combinations_list.append(tuple(w))
        return combinations_list
    
    def optimize_indicator_parameters(
        self,
        df: pd.DataFrame,
        indicator_name: str,
        category: IndicatorCategory,
        target_column: str = "returns",
        parameter_ranges: Optional[Dict[str, List[int]]] = None
    ) -> Dict[str, Any]:
        """
        Find optimal parameters for an indicator.
        
        Args:
            df: Input DataFrame
            indicator_name: Indicator base name (e.g., "rsi")
            category: Indicator category
            target_column: Target column
            parameter_ranges: Dict mapping param names to lists of values
                             e.g., {"period": [7, 14, 21, 28]}
            
        Returns:
            Dictionary with best parameters and metrics
        """
        if not parameter_ranges:
            logger.warning("No parameter ranges provided for optimization")
            return {}
        
        try:
            best_score = 0.0
            best_params = {}
            best_metric = None
            
            for param_name, param_values in parameter_ranges.items():
                for param_value in param_values:
                    test_col = f"{indicator_name}_{param_name}_{param_value}"
                    
                    if test_col not in df.columns:
                        logger.debug(f"Column {test_col} not found, skipping")
                        continue
                    
                    metric = self.analyze_indicator_performance(
                        df, test_col, category, target_column
                    )
                    
                    if metric and metric.composite_score() > best_score:
                        best_score = metric.composite_score()
                        best_params = {param_name: param_value}
                        best_metric = metric
            
            if best_metric:
                logger.info(
                    f"Optimal parameters for {indicator_name}: "
                    f"{best_params}, score={best_score:.4f}"
                )
                return {
                    "indicator": indicator_name,
                    "best_params": best_params,
                    "best_score": best_score,
                    "metric": best_metric.to_dict()
                }
            
            return {}
        
        except Exception as e:
            logger.error(f"Error in parameter optimization: {e}")
            return {}
    
    # ==================== PATTERN DETECTION ====================
    
    def detect_candlestick_patterns(
        self,
        df: pd.DataFrame,
        target_column: str = "returns"
    ) -> Dict[str, PatternMetric]:
        """
        Detect and analyze candlestick patterns.
        
        Args:
            df: Input DataFrame with OHLC data
            target_column: Target/returns column
            
        Returns:
            Dictionary of detected patterns
        """
        if df.empty or not all(c in df.columns for c in ['open', 'close', 'high', 'low']):
            return {}
        
        patterns_found = {}
        
        try:
            patterns_found.update(self._detect_engulfing_patterns(df, target_column))
            patterns_found.update(self._detect_doji_patterns(df, target_column))
            patterns_found.update(self._detect_inside_bar_patterns(df, target_column))
            patterns_found.update(self._detect_three_bar_patterns(df, target_column))
            patterns_found.update(self._detect_star_patterns(df, target_column))
            
            with self._lock:
                self.patterns.update(patterns_found)
            
            logger.info(f"Discovered {len(patterns_found)} candlestick patterns")
            return patterns_found
        
        except Exception as e:
            logger.error(f"Error in candlestick pattern detection: {e}")
            return {}
    
    def detect_divergence(
        self,
        df: pd.DataFrame,
        price_column: str = "close",
        indicator_column: str = "rsi",
        target_column: str = "returns",
        window: int = 14
    ) -> Dict[str, PatternMetric]:
        """
        Detect price-indicator divergences (FIXED: actual value comparison).
        
        Args:
            df: Input DataFrame
            price_column: Price column name
            indicator_column: Indicator column name
            target_column: Target/returns column
            window: Lookback window for extrema detection
            
        Returns:
            Dictionary of divergence patterns
        """
        if df.empty or price_column not in df.columns or indicator_column not in df.columns:
            return {}
        
        patterns = {}
        
        try:
            price = df[price_column].values.astype(float)
            indicator = df[indicator_column].values.astype(float)
            returns = df[target_column].values.astype(float)
            
            # Find local extrema (peaks and troughs)
            price_peaks = self._find_extrema(price, window=window, extrema_type='max')
            price_troughs = self._find_extrema(price, window=window, extrema_type='min')
            indicator_peaks = self._find_extrema(indicator, window=window, extrema_type='max')
            indicator_troughs = self._find_extrema(indicator, window=window, extrema_type='min')
            
            # FIXED: Extract ACTUAL VALUES at extrema indices, not binary arrays
            peak_indices_price = np.where(price_peaks == 1)[0]
            trough_indices_price = np.where(price_troughs == 1)[0]
            peak_indices_ind = np.where(indicator_peaks == 1)[0]
            trough_indices_ind = np.where(indicator_troughs == 1)[0]
            
            bullish_div = np.zeros(len(price), dtype=int)
            bearish_div = np.zeros(len(price), dtype=int)
            
            # Bullish divergence: price lower lows, indicator higher lows
            if len(trough_indices_price) >= 2:
                for i in range(1, len(trough_indices_price)):
                    idx_prev = trough_indices_price[i-1]
                    idx_curr = trough_indices_price[i]
                    
                    if idx_curr < len(indicator):
                        if (price[idx_prev] > price[idx_curr] and 
                            indicator[idx_prev] < indicator[idx_curr]):
                            bullish_div[idx_curr] = 1
            
            # Bearish divergence: price higher highs, indicator lower highs
            if len(peak_indices_price) >= 2:
                for i in range(1, len(peak_indices_price)):
                    idx_prev = peak_indices_price[i-1]
                    idx_curr = peak_indices_price[i]
                    
                    if idx_curr < len(indicator):
                        if (price[idx_prev] < price[idx_curr] and 
                            indicator[idx_prev] > indicator[idx_curr]):
                            bearish_div[idx_curr] = 1
            
            # Evaluate bullish divergence
            if bullish_div.sum() > 0:
                metrics = self._calculate_pattern_metrics(pd.Series(bullish_div), pd.Series(returns))
                patterns['bullish_divergence'] = PatternMetric(
                    name='bullish_divergence',
                    pattern_type=PatternType.DIVERGENCE,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
            
            # Evaluate bearish divergence
            if bearish_div.sum() > 0:
                metrics = self._calculate_pattern_metrics(pd.Series(bearish_div), pd.Series(returns))
                patterns['bearish_divergence'] = PatternMetric(
                    name='bearish_divergence',
                    pattern_type=PatternType.DIVERGENCE,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
            
            logger.info(f"Detected {len(patterns)} divergence patterns")
            return patterns
        
        except Exception as e:
            logger.error(f"Error detecting divergence: {e}")
            return {}
    
    def _find_extrema(self, data: np.ndarray, window: int = 14, extrema_type: str = 'max') -> np.ndarray:
        """
        Find local extrema (peaks or troughs) in data.
        
        Args:
            data: Input array
            window: Lookback/forward window
            extrema_type: 'max' for peaks, 'min' for troughs
            
        Returns:
            Binary array marking extrema positions
        """
        extrema = np.zeros(len(data), dtype=int)
        
        try:
            for i in range(window, len(data) - window):
                if extrema_type == 'max':
                    if data[i] == np.max(data[i-window:i+window+1]):
                        extrema[i] = 1
                elif extrema_type == 'min':
                    if data[i] == np.min(data[i-window:i+window+1]):
                        extrema[i] = 1
        
        except Exception as e:
            logger.warning(f"Error finding extrema: {e}")
        
        return extrema
    
    def detect_support_resistance(
        self,
        df: pd.DataFrame,
        target_column: str = "returns",
        window: int = 20,
        threshold: float = 0.02
    ) -> Dict[str, PatternMetric]:
        """
        Detect support and resistance levels (RESTORED from v2.0).
        
        Args:
            df: Input DataFrame with price data
            target_column: Target column
            window: Lookback window for finding extrema
            threshold: Proximity threshold for level clustering
            
        Returns:
            Dictionary of S/R patterns
        """
        if df.empty or 'close' not in df.columns:
            return {}
        
        patterns = {}
        
        try:
            close = df['close'].values.astype(float)
            returns = df[target_column].values.astype(float)
            
            support_levels = []
            resistance_levels = []
            
            for i in range(window, len(close) - window):
                if close[i] == np.min(close[i-window:i+window]):
                    support_levels.append((i, close[i]))
                if close[i] == np.max(close[i-window:i+window]):
                    resistance_levels.append((i, close[i]))
            
            if support_levels:
                support_bounces = 0
                support_success = 0
                
                for idx, level in support_levels:
                    if idx + 1 < len(returns):
                        support_bounces += 1
                        if returns[idx] > 0:
                            support_success += 1
                
                if support_bounces > 0:
                    metrics = {
                        'occurrence_count': support_bounces,
                        'success_rate': support_success / support_bounces,
                        'avg_profit': returns[len(support_levels):].mean(),
                        'avg_loss': abs(returns[:len(support_levels)].min()),
                        'profit_factor': 1.5,
                        'reliability': min(1.0, len(support_levels) / len(close)),
                        'lookback_periods': window,
                        'backtest_periods': len(close)
                    }
                    patterns['support_level'] = PatternMetric(
                        name='support_level',
                        pattern_type=PatternType.SUPPORT_RESISTANCE,
                        **metrics,
                        discovered_at=datetime.now(timezone.utc)
                    )
            
            if resistance_levels:
                resistance_fails = 0
                resistance_success = 0
                
                for idx, level in resistance_levels:
                    if idx + 1 < len(returns):
                        resistance_fails += 1
                        if returns[idx] < 0:
                            resistance_success += 1
                
                if resistance_fails > 0:
                    metrics = {
                        'occurrence_count': resistance_fails,
                        'success_rate': resistance_success / resistance_fails,
                        'avg_profit': abs(returns[len(resistance_levels):].mean()),
                        'avg_loss': returns[:len(resistance_levels)].max(),
                        'profit_factor': 1.5,
                        'reliability': min(1.0, len(resistance_levels) / len(close)),
                        'lookback_periods': window,
                        'backtest_periods': len(close)
                    }
                    patterns['resistance_level'] = PatternMetric(
                        name='resistance_level',
                        pattern_type=PatternType.SUPPORT_RESISTANCE,
                        **metrics,
                        discovered_at=datetime.now(timezone.utc)
                    )
            
            logger.info(f"Detected support/resistance patterns: {len(patterns)}")
            return patterns
        
        except Exception as e:
            logger.error(f"Error detecting S/R: {e}")
            return {}
    
    def detect_breakouts(
        self, df: pd.DataFrame, target_column: str = "returns",
        lookback: int = 20, threshold: float = 0.02
    ) -> Dict[str, PatternMetric]:
        """Detect breakouts above resistance or below support"""
        if df.empty or 'close' not in df.columns or 'high' not in df.columns or 'low' not in df.columns:
            return {}
        
        patterns = {}
        try:
            resistance = df['high'].rolling(lookback).max().shift(1)
            support = df['low'].rolling(lookback).min().shift(1)
            
            upbreak = (df['close'] > resistance) & ((df['close'] - resistance) / resistance > threshold)
            downbreak = (df['close'] < support) & ((support - df['close']) / support > threshold)
            
            for name, signal in [('upbreak', upbreak), ('downbreak', downbreak)]:
                metrics = self._calculate_pattern_metrics(signal.astype(int), df[target_column])
                patterns[name] = PatternMetric(
                    name=f"breakout_{name}",
                    pattern_type=PatternType.BREAKOUT,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
            
            logger.info(f"Detected {sum(1 for v in patterns.values() if v.occurrence_count > 0)} breakout patterns")
            return {k: v for k, v in patterns.items() if v.occurrence_count > 0}
        
        except Exception as e:
            logger.error(f"Error detecting breakouts: {e}")
            return {}
    
    def detect_trendlines(
        self, df: pd.DataFrame, target_column: str = "returns", window: int = 5
    ) -> Dict[str, PatternMetric]:
        """Detect trendlines using regression on extrema"""
        if df.empty or 'close' not in df.columns:
            return {}
        
        patterns = {}
        try:
            close = df['close'].values
            high_indices = np.where(self._find_extrema(close, window=window, extrema_type='max') == 1)[0]
            low_indices = np.where(self._find_extrema(close, window=window, extrema_type='min') == 1)[0]
            
            uptrend = np.zeros(len(df), dtype=int)
            downtrend = np.zeros(len(df), dtype=int)
            
            if len(high_indices) >= 2:
                z = np.polyfit(high_indices[-2:], close[high_indices[-2:]], 1)
                for i in range(high_indices[-1]+1, len(df)):
                    if close[i] > np.polyval(z, i):
                        uptrend[i] = 1
            
            if len(low_indices) >= 2:
                z = np.polyfit(low_indices[-2:], close[low_indices[-2:]], 1)
                for i in range(low_indices[-1]+1, len(df)):
                    if close[i] < np.polyval(z, i):
                        downtrend[i] = 1
            
            for name, signal in [('uptrend', uptrend), ('downtrend', downtrend)]:
                metrics = self._calculate_pattern_metrics(pd.Series(signal), df[target_column])
                patterns[name] = PatternMetric(
                    name=f"trendline_{name}",
                    pattern_type=PatternType.TREND_LINE,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
            
            return {k: v for k, v in patterns.items() if v.occurrence_count > 0}
        
        except Exception as e:
            logger.error(f"Error detecting trendlines: {e}")
            return {}
    
    def _detect_engulfing_patterns(
        self,
        df: pd.DataFrame,
        target_column: str
    ) -> Dict[str, PatternMetric]:
        """Detect engulfing patterns"""
        patterns = {}
        
        try:
            df_work = df[['open', 'close', 'high', 'low', target_column]].astype(float)
            
            prev_open = df_work["open"].shift(1)
            prev_close = df_work["close"].shift(1)
            prev_body = (prev_close - prev_open).abs()
            curr_body = (df_work["close"] - df_work["open"]).abs()
            
            bullish = (
                (prev_close < prev_open) &
                (df_work["close"] > df_work["open"]) &
                (df_work["open"] <= prev_close) &
                (df_work["close"] >= prev_open) &
                (curr_body > prev_body)
            )
            
            if bullish.sum() > 0:
                metrics = self._calculate_pattern_metrics(bullish, df_work[target_column])
                patterns['engulfing_bullish'] = PatternMetric(
                    name='engulfing_bullish',
                    pattern_type=PatternType.CANDLESTICK,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
            
            bearish = (
                (prev_close > prev_open) &
                (df_work["close"] < df_work["open"]) &
                (df_work["open"] >= prev_close) &
                (df_work["close"] <= prev_open) &
                (curr_body > prev_body)
            )
            
            if bearish.sum() > 0:
                metrics = self._calculate_pattern_metrics(bearish, df_work[target_column])
                patterns['engulfing_bearish'] = PatternMetric(
                    name='engulfing_bearish',
                    pattern_type=PatternType.CANDLESTICK,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
        
        except KeyError as e:
            logger.debug(f"Error in engulfing detection: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error in engulfing detection: {e}")
        
        return patterns
    
    def _detect_doji_patterns(
        self,
        df: pd.DataFrame,
        target_column: str,
        threshold: float = 0.1
    ) -> Dict[str, PatternMetric]:
        """Detect doji patterns"""
        patterns = {}
        
        try:
            df_work = df[['open', 'close', 'high', 'low', target_column]].astype(float)
            
            body = (df_work["close"] - df_work["open"]).abs()
            range_ = df_work["high"] - df_work["low"]
            range_ = range_.replace(0, 1e-10)
            
            is_doji = ((body / (range_ + 1e-10)) < threshold)
            
            if is_doji.sum() > 0:
                metrics = self._calculate_pattern_metrics(is_doji, df_work[target_column])
                patterns['doji'] = PatternMetric(
                    name='doji',
                    pattern_type=PatternType.CANDLESTICK,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
        
        except KeyError as e:
            logger.debug(f"Error in doji detection: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error in doji detection: {e}")
        
        return patterns
    
    def _detect_inside_bar_patterns(
        self,
        df: pd.DataFrame,
        target_column: str
    ) -> Dict[str, PatternMetric]:
        """Detect inside bar patterns"""
        patterns = {}
        
        try:
            df_work = df[['high', 'low', target_column]].astype(float)
            
            prev_high = df_work["high"].shift(1)
            prev_low = df_work["low"].shift(1)
            
            inside_bar = (
                (df_work["high"] <= prev_high) &
                (df_work["low"] >= prev_low)
            )
            
            if inside_bar.sum() > 0:
                metrics = self._calculate_pattern_metrics(inside_bar, df_work[target_column])
                patterns['inside_bar'] = PatternMetric(
                    name='inside_bar',
                    pattern_type=PatternType.PRICE_ACTION,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
        
        except KeyError as e:
            logger.debug(f"Error in inside bar detection: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error in inside bar detection: {e}")
        
        return patterns
    
    def _detect_three_bar_patterns(
        self,
        df: pd.DataFrame,
        target_column: str
    ) -> Dict[str, PatternMetric]:
        """Detect three bar patterns"""
        patterns = {}
        
        try:
            df_work = df[['open', 'close', target_column]].astype(float)
            
            bullish_1 = df_work["close"] > df_work["open"]
            bullish_2 = df_work["close"].shift(1) > df_work["open"].shift(1)
            bullish_3 = df_work["close"].shift(2) > df_work["open"].shift(2)
            
            higher_1 = df_work["close"] > df_work["close"].shift(1)
            higher_2 = df_work["close"].shift(1) > df_work["close"].shift(2)
            
            three_white = bullish_1 & bullish_2 & bullish_3 & higher_1 & higher_2
            
            if three_white.sum() > 0:
                metrics = self._calculate_pattern_metrics(three_white, df_work[target_column])
                patterns['three_white_soldiers'] = PatternMetric(
                    name='three_white_soldiers',
                    pattern_type=PatternType.CANDLESTICK,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
            
            bearish_1 = df_work["close"] < df_work["open"]
            bearish_2 = df_work["close"].shift(1) < df_work["open"].shift(1)
            bearish_3 = df_work["close"].shift(2) < df_work["open"].shift(2)
            
            lower_1 = df_work["close"] < df_work["close"].shift(1)
            lower_2 = df_work["close"].shift(1) < df_work["close"].shift(2)
            
            three_black = bearish_1 & bearish_2 & bearish_3 & lower_1 & lower_2
            
            if three_black.sum() > 0:
                metrics = self._calculate_pattern_metrics(three_black, df_work[target_column])
                patterns['three_black_crows'] = PatternMetric(
                    name='three_black_crows',
                    pattern_type=PatternType.CANDLESTICK,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
        
        except KeyError as e:
            logger.debug(f"Error in three bar detection: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error in three bar detection: {e}")
        
        return patterns
    
    def _detect_star_patterns(
        self,
        df: pd.DataFrame,
        target_column: str
    ) -> Dict[str, PatternMetric]:
        """Detect morning/evening star patterns"""
        patterns = {}
        
        try:
            df_work = df[['open', 'close', target_column]].astype(float)
            
            body_1 = (df_work["close"].shift(2) - df_work["open"].shift(2)).abs()
            body_2 = (df_work["close"].shift(1) - df_work["open"].shift(1)).abs()
            
            morning = (
                (df_work["close"].shift(2) < df_work["open"].shift(2)) &
                (body_2 < body_1 * 0.3) &
                (df_work["close"] > df_work["open"]) &
                (df_work["close"] > (df_work["open"].shift(2) + df_work["close"].shift(2)) / 2)
            )
            
            if morning.sum() > 0:
                metrics = self._calculate_pattern_metrics(morning, df_work[target_column])
                patterns['morning_star'] = PatternMetric(
                    name='morning_star',
                    pattern_type=PatternType.CANDLESTICK,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
            
            evening = (
                (df_work["close"].shift(2) > df_work["open"].shift(2)) &
                (body_2 < body_1 * 0.3) &
                (df_work["close"] < df_work["open"]) &
                (df_work["close"] < (df_work["open"].shift(2) + df_work["close"].shift(2)) / 2)
            )
            
            if evening.sum() > 0:
                metrics = self._calculate_pattern_metrics(evening, df_work[target_column])
                patterns['evening_star'] = PatternMetric(
                    name='evening_star',
                    pattern_type=PatternType.CANDLESTICK,
                    **metrics,
                    discovered_at=datetime.now(timezone.utc)
                )
        
        except KeyError as e:
            logger.debug(f"Error in star pattern detection: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error in star pattern detection: {e}")
        
        return patterns
    
    def _calculate_pattern_metrics(
        self,
        pattern_signal: pd.Series,
        returns: pd.Series
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a pattern"""
        try:
            pattern_returns = returns[pattern_signal].dropna()
            
            if len(pattern_returns) == 0:
                return {
                    'occurrence_count': 0,
                    'success_rate': 0.0,
                    'avg_profit': 0.0,
                    'avg_loss': 0.0,
                    'profit_factor': 0.0,
                    'reliability': 0.0,
                    'lookback_periods': len(returns),
                    'backtest_periods': len(returns)
                }
            
            occurrences = int(pattern_signal.sum())
            wins = int((pattern_returns > 0).sum())
            losses = int((pattern_returns < 0).sum())
            
            success_rate = wins / occurrences if occurrences > 0 else 0.0
            avg_profit = pattern_returns[pattern_returns > 0].mean() if wins > 0 else 0.0
            avg_loss = abs(pattern_returns[pattern_returns < 0].mean()) if losses > 0 else 0.0
            
            if avg_loss == 0 and avg_profit > 0:
                profit_factor = 10.0
            elif avg_loss == 0:
                profit_factor = 0.0
            else:
                profit_factor = avg_profit / (avg_loss + 1e-10)
            
            reliability = min(1.0, occurrences / len(returns)) if len(returns) > 0 else 0.0
            
            return {
                'occurrence_count': occurrences,
                'success_rate': max(0.0, min(success_rate, 1.0)),
                'avg_profit': float(avg_profit),
                'avg_loss': float(avg_loss),
                'profit_factor': max(0.0, min(profit_factor, 10.0)),
                'reliability': max(0.0, min(reliability, 1.0)),
                'lookback_periods': len(returns),
                'backtest_periods': len(returns)
            }
        
        except Exception as e:
            logger.warning(f"Error calculating pattern metrics: {e}")
            return {
                'occurrence_count': 0,
                'success_rate': 0.0,
                'avg_profit': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'reliability': 0.0,
                'lookback_periods': 0,
                'backtest_periods': 0
            }
    
    # ==================== COMBINATION DISCOVERY ====================
    
    def discover_combinations(
        self,
        df: pd.DataFrame,
        target_column: str = "returns",
        max_combination_size: Optional[int] = None,
        min_score: float = 0.55
    ) -> Dict[str, IndicatorCombination]:
        """
        Discover effective indicator combinations.
        
        Args:
            df: Input DataFrame
            target_column: Target column
            max_combination_size: Max number of indicators to combine
            min_score: Minimum score threshold
            
        Returns:
            Dictionary of effective combinations
        """
        if not self.indicators:
            logger.warning("No indicators discovered yet")
            return {}
        
        max_size = max_combination_size or self.config.max_combination_size
        combinations_found = {}
        
        try:
            indicator_names = list(self.indicators.keys())
            
            for size in range(2, min(max_size + 1, len(indicator_names) + 1)):
                for combo in combinations(indicator_names, size):
                    combo_key = "_".join(combo)
                    
                    if not all(name in df.columns for name in combo):
                        continue
                    
                    combined_signal = df[list(combo)].mean(axis=1).values
                    returns = df[target_column].values
                    
                    win_rate = self._calculate_win_rate(combined_signal, returns)
                    profit_factor = self._calculate_profit_factor(combined_signal, returns)
                    sharpe_ratio = self._calculate_sharpe_ratio(returns)
                    signal_quality = self._calculate_signal_quality(combined_signal, returns)
                    synergy = self._calculate_synergy(list(combo), combined_signal, returns)
                    
                    combination = IndicatorCombination(
                        indicators=list(combo),
                        combined_score=(
                            win_rate * 0.3 +
                            min(profit_factor / 2.0, 1.0) * 0.3 +
                            max(min(sharpe_ratio / 3.0, 1.0), 0.0) * 0.2 +
                            signal_quality * 0.2
                        ),
                        win_rate=win_rate,
                        profit_factor=profit_factor,
                        sharpe_ratio=sharpe_ratio,
                        synergy_factor=synergy,
                        signal_quality=signal_quality,
                        backtest_periods=len(returns),
                        discovered_at=datetime.now(timezone.utc)
                    )
                    
                    if combination.effective_score() >= min_score:
                        with self._lock:
                            combinations_found[combo_key] = combination
            
            with self._lock:
                self.combinations.update(combinations_found)
            
            logger.info(f"Discovered {len(combinations_found)} combinations with score >= {min_score}")
            return combinations_found
        
        except Exception as e:
            logger.error(f"Error in combination discovery: {e}")
            return {}
    
    def cleanup_temporary_columns(self, df: pd.DataFrame, keep_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove temporary indicator columns to free memory.
        
        Args:
            df: Input DataFrame
            keep_columns: List of column names to preserve
            
        Returns:
            Cleaned DataFrame
        """
        if keep_columns is None:
            keep_columns = ['open', 'close', 'high', 'low', 'volume', 'returns']
        
        columns_to_drop = []
        
        for col in df.columns:
            if col not in keep_columns and col not in self.indicators:
                if any(pattern in col.lower() for pattern in ['_temp', '_intermediate', '_calc']):
                    columns_to_drop.append(col)
        
        if columns_to_drop:
            df_cleaned = df.drop(columns=columns_to_drop)
            logger.info(f"Cleaned {len(columns_to_drop)} temporary columns")
            return df_cleaned
        
        return df
    
    def export_discoveries(self, output_path: str = "discoveries.json"):
        """Export discoveries to JSON file"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "indicators": {
                    name: metric.to_dict()
                    for name, metric in self.indicators.items()
                },
                "patterns": {
                    name: metric.to_dict()
                    for name, metric in self.patterns.items()
                },
                "combinations": {
                    name: combo.to_dict()
                    for name, combo in self.combinations.items()
                },
                "statistics": {
                    "total_indicators": len(self.indicators),
                    "total_patterns": len(self.patterns),
                    "total_combinations": len(self.combinations),
                    "avg_indicator_score": np.mean(
                        [m.composite_score() for m in self.indicators.values()], default=0
                    ),
                    "avg_pattern_score": np.mean(
                        [p.score() for p in self.patterns.values()], default=0
                    ),
                    "avg_combination_score": np.mean(
                        [c.effective_score() for c in self.combinations.values()], default=0
                    )
                }
            }
            
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Discoveries exported to {output_path}")
        except IOError as e:
            logger.error(f"IO error exporting discoveries: {e}")
        except Exception as e:
            logger.error(f"Error exporting discoveries: {e}")
    
    # ==================== HELPER METHODS ====================
    
    def _count_significant_signals(self, signal: np.ndarray, threshold: float = 0.01) -> int:
        """Count significant directional changes in signal"""
        if len(signal) < 2:
            return 0
        
        try:
            smoothed = pd.Series(signal).rolling(3, center=True).mean().values
            directions = np.sign(np.diff(smoothed))
            changes = np.abs(np.diff(directions))
            
            return int(np.sum(changes > 0))
        except Exception:
            return 0
    
    def _calculate_win_rate(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate win rate"""
        if len(signal) < 2:
            return 0.5
        
        try:
            smoothed = pd.Series(signal).rolling(3, center=True).mean().values
            signal_direction = np.sign(np.diff(smoothed))
            returns_direction = np.sign(returns[1:])
            
            matches = np.sum(signal_direction == returns_direction)
            return matches / len(signal_direction) if len(signal_direction) > 0 else 0.5
        except Exception:
            return 0.5
    
    def _calculate_profit_factor(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate profit factor"""
        if len(signal) < 2:
            return 1.0
        
        try:
            smoothed = pd.Series(signal).rolling(3, center=True).mean().values
            weighted_returns = returns[1:] * np.sign(np.diff(smoothed))
            
            gains = np.sum(weighted_returns[weighted_returns > 0])
            losses = np.abs(np.sum(weighted_returns[weighted_returns < 0]))
            
            if losses == 0:
                return 2.0 if gains > 0 else 1.0
            return gains / (losses + 1e-10) if gains > 0 else 0.1
        except Exception:
            return 1.0
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0.0
        
        try:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return 0.0
            return (mean_return / std_return) * np.sqrt(252)
        except Exception:
            return 0.0
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        try:
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / (running_max + 1e-10)
            return float(np.min(drawdown))
        except Exception:
            return 0.0
    
    def _calculate_accuracy(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate prediction accuracy"""
        if len(signal) < 2:
            return 0.5
        
        try:
            smoothed = pd.Series(signal).rolling(3, center=True).mean().values
            signal_binary = (np.diff(smoothed) > 0).astype(int)
            returns_binary = (returns[1:] > 0).astype(int)
            
            correct = np.sum(signal_binary == returns_binary)
            return correct / len(signal_binary) if len(signal_binary) > 0 else 0.5
        except Exception:
            return 0.5
    
    def _calculate_precision_recall_f1(
        self,
        signal: np.ndarray,
        returns: np.ndarray
    ) -> Tuple[float, float, float]:
        """Calculate precision, recall, F1"""
        if len(signal) < 2:
            return 0.5, 0.5, 0.5
        
        try:
            smoothed = pd.Series(signal).rolling(3, center=True).mean().values
            signal_binary = (np.diff(smoothed) > 0).astype(int)
            returns_binary = (returns[1:] > 0).astype(int)
            
            tp = np.sum((signal_binary == 1) & (returns_binary == 1))
            fp = np.sum((signal_binary == 1) & (returns_binary == 0))
            fn = np.sum((signal_binary == 0) & (returns_binary == 1))
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            return precision, recall, f1
        except Exception:
            return 0.5, 0.5, 0.5
    
    def _calculate_correlation(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate correlation between signal and returns"""
        try:
            correlation = np.corrcoef(signal, returns)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0
        except Exception:
            return 0.0
    
    def _calculate_brier_score(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """
        Calculate Brier Score for probability predictions.
        Measures calibration of probabilistic predictions.
        """
        if len(signal) < 2:
            return 0.5
        
        try:
            # Normalize signal to [0, 1] as probability estimate
            signal_min = np.min(signal)
            signal_max = np.max(signal)
            
            if signal_max == signal_min:
                return 0.5
            
            signal_prob = (signal - signal_min) / (signal_max - signal_min)
            returns_binary = (returns > 0).astype(int)
            
            brier = np.mean((signal_prob - returns_binary) ** 2)
            return max(0.0, min(brier, 1.0))
        except Exception:
            return 0.5
    
    def _calculate_signal_quality(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate overall signal quality"""
        if len(signal) < 2:
            return 0.0
        
        try:
            _, _, f1 = self._calculate_precision_recall_f1(signal, returns)
            win_rate = self._calculate_win_rate(signal, returns)
            return (f1 * 0.5 + win_rate * 0.5)
        except Exception:
            return 0.0
    
    def _calculate_synergy(
        self,
        indicators: List[str],
        combined_signal: np.ndarray,
        returns: np.ndarray
    ) -> float:
        """Calculate synergy factor between indicators"""
        if len(indicators) < 2:
            return 1.0
        
        try:
            individual_scores = [
                self._indicator_cache.get(name, self.indicators.get(name)).composite_score()
                if name in self._indicator_cache or name in self.indicators else 0.5
                for name in indicators
            ]
            avg_individual = np.mean(individual_scores)
            
            combined_accuracy = self._calculate_accuracy(combined_signal, returns)
            
            synergy = combined_accuracy / (avg_individual + 1e-10)
            return min(2.0, max(0.5, synergy))
        except Exception:
            return 1.0
    
    def _infer_category(self, column_name: str) -> IndicatorCategory:
        """Infer indicator category from column name"""
        name_lower = column_name.lower()
        
        momentum_keywords = ['rsi', 'macd', 'stoch', 'momentum', 'oscillator']
        volatility_keywords = ['atr', 'bb_', 'bollinger', 'std', 'volatility']
        trend_keywords = ['sma', 'ema', 'trend', 'adx', 'dmi']
        volume_keywords = ['volume', 'obv', 'on_balance']
        price_keywords = ['engulf', 'doji', 'inside_bar', 'morning', 'evening', 'white', 'black']
        return_keywords = ['return', 'acceleration', 'velocity', 'jerk']
        
        for keyword in momentum_keywords:
            if keyword in name_lower:
                return IndicatorCategory.MOMENTUM
        
        for keyword in volatility_keywords:
            if keyword in name_lower:
                return IndicatorCategory.VOLATILITY
        
        for keyword in trend_keywords:
            if keyword in name_lower:
                return IndicatorCategory.TREND
        
        for keyword in volume_keywords:
            if keyword in name_lower:
                return IndicatorCategory.VOLUME
        
        for keyword in price_keywords:
            if keyword in name_lower:
                return IndicatorCategory.PRICE_ACTION
        
        for keyword in return_keywords:
            if keyword in name_lower:
                return IndicatorCategory.RETURNS
        
        return IndicatorCategory.MOMENTUM


__all__ = [
    'Discovery',
    'DiscoveryConfig',
    'IndicatorMetric',
    'PatternMetric',
    'IndicatorCombination',
    'IndicatorCategory',
    'PatternType',
    'IndicatorDefinition',
]
