"""
Trading AI System - Discovery Module
Automated discovery and ranking of technical indicators, price patterns, and features.

Supports:
- Indicator performance analysis and ranking
- Technical pattern discovery
- Feature combination optimization
- Synergy detection between indicators
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import json
from pathlib import Path
import numpy as np
import pandas as pd
from itertools import combinations
from threading import Lock

logger = logging.getLogger(__name__)


class IndicatorCategory(Enum):
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    TREND = "trend"
    VOLUME = "volume"
    PRICE_ACTION = "price_action"
    RETURNS = "returns"


class PatternType(Enum):
    CANDLESTICK = "candlestick"
    PRICE_ACTION = "price_action"
    SUPPORT_RESISTANCE = "support_resistance"
    TREND_LINE = "trend_line"
    DIVERGENCE = "divergence"
    BREAKOUT = "breakout"


@dataclass
class IndicatorMetric:
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
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: Optional[datetime] = None
    
    def composite_score(self) -> float:
        """Calculate composite performance score"""
        weights = {
            'win_rate': 0.25,
            'profit_factor': 0.25,
            'sharpe_ratio': 0.20,
            'f1_score': 0.20,
            'correlation': 0.10
        }
        
        score = (
            self.win_rate * weights['win_rate'] +
            min(self.profit_factor / 2.0, 1.0) * weights['profit_factor'] +
            max(min(self.sharpe_ratio / 3.0, 1.0), 0.0) * weights['sharpe_ratio'] +
            self.f1_score * weights['f1_score'] +
            abs(self.correlation_with_returns) * weights['correlation']
        )
        return max(0.0, min(score, 1.0))
    
    def to_dict(self) -> Dict[str, Any]:
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
            "composite_score": self.composite_score(),
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None
        }


@dataclass
class PatternMetric:
    name: str
    pattern_type: PatternType
    occurrence_count: int = 0
    success_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    reliability: float = 0.0
    lookback_periods: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: Optional[datetime] = None
    
    def score(self) -> float:
        """Calculate pattern score"""
        if self.occurrence_count < 5:
            return 0.0
        
        score = (
            self.success_rate * 0.4 +
            min(self.profit_factor / 2.0, 1.0) * 0.4 +
            self.reliability * 0.2
        )
        return max(0.0, min(score, 1.0))
    
    def to_dict(self) -> Dict[str, Any]:
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
            "score": self.score(),
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None
        }


@dataclass
class IndicatorCombination:
    indicators: List[str]
    combined_score: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    synergy_factor: float = 1.0
    signal_quality: float = 0.0
    backtest_periods: int = 0
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
        return {
            "indicators": self.indicators,
            "combined_score": self.combined_score,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "sharpe_ratio": self.sharpe_ratio,
            "synergy_factor": self.synergy_factor,
            "signal_quality": self.signal_quality,
            "backtest_periods": self.backtest_periods,
            "effective_score": self.effective_score(),
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "metadata": self.metadata
        }


class Discovery:
    """Automated discovery system for indicators, patterns, and features"""
    
    def __init__(self, min_samples: int = 100, confidence_threshold: float = 0.55):
        self.min_samples = min_samples
        self.confidence_threshold = confidence_threshold
        self.indicators: Dict[str, IndicatorMetric] = {}
        self.patterns: Dict[str, PatternMetric] = {}
        self.combinations: Dict[str, IndicatorCombination] = {}
        self._lock = Lock()
        self.discovery_history: List[Dict[str, Any]] = []
    
    # ==================== INDICATOR DISCOVERY ====================
    
    def analyze_indicator_performance(
        self,
        df: pd.DataFrame,
        indicator_name: str,
        category: IndicatorCategory,
        target_column: str = "returns",
        min_periods: int = 10
    ) -> Optional[IndicatorMetric]:
        """Analyze single indicator performance"""
        
        if not isinstance(df, pd.DataFrame) or df.empty:
            logger.warning(f"Invalid DataFrame for {indicator_name}")
            return None
        
        if indicator_name not in df.columns:
            logger.warning(f"Indicator {indicator_name} not found in DataFrame")
            return None
        
        if target_column not in df.columns:
            logger.warning(f"Target column {target_column} not found")
            return None
        
        try:
            df_work = df[[indicator_name, target_column]].dropna()
            
            if len(df_work) < self.min_samples:
                logger.warning(f"Insufficient data for {indicator_name}: {len(df_work)} < {self.min_samples}")
                return None
            
            indicator_values = df_work[indicator_name].values
            returns = df_work[target_column].values
            
            win_rate = self._calculate_win_rate(indicator_values, returns)
            profit_factor = self._calculate_profit_factor(indicator_values, returns)
            sharpe_ratio = self._calculate_sharpe_ratio(indicator_values, returns)
            max_drawdown = self._calculate_max_drawdown(indicator_values, returns)
            accuracy = self._calculate_accuracy(indicator_values, returns)
            precision, recall, f1 = self._calculate_precision_recall_f1(indicator_values, returns)
            correlation = np.corrcoef(indicator_values, returns)[0, 1]
            
            if np.isnan(correlation):
                correlation = 0.0
            
            signals = np.sum(np.abs(np.diff(np.sign(np.diff(indicator_values)))) > 0) if len(indicator_values) > 2 else 0
            
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
                frequency=len(df_work),
                signals_generated=int(signals),
                discovered_at=datetime.now(timezone.utc),
                metadata={
                    "data_points": len(df_work),
                    "indicator_range": (float(np.min(indicator_values)), float(np.max(indicator_values))),
                    "returns_range": (float(np.min(returns)), float(np.max(returns)))
                }
            )
            
            with self._lock:
                self.indicators[indicator_name] = metric
            
            logger.info(f"Analyzed {indicator_name}: score={metric.composite_score():.4f}")
            return metric
        
        except Exception as e:
            logger.error(f"Error analyzing {indicator_name}: {e}")
            return None
    
    def discover_indicators(
        self,
        df: pd.DataFrame,
        target_column: str = "returns",
        min_score: float = 0.5
    ) -> Dict[str, IndicatorMetric]:
        """Discover and rank all available indicators"""
        
        if df.empty:
            logger.warning("Empty DataFrame provided")
            return {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if target_column in numeric_cols:
            numeric_cols.remove(target_column)
        
        discovered = {}
        
        for col in numeric_cols:
            inferred_category = self._infer_category(col)
            metric = self.analyze_indicator_performance(df, col, inferred_category, target_column)
            
            if metric and metric.composite_score() >= min_score:
                discovered[col] = metric
        
        logger.info(f"Discovered {len(discovered)} indicators with score >= {min_score}")
        return discovered
    
    # ==================== PATTERN DISCOVERY ====================
    
    def detect_candlestick_patterns(
        self,
        df: pd.DataFrame,
        target_column: str = "returns"
    ) -> Dict[str, PatternMetric]:
        """Detect and analyze candlestick patterns"""
        
        if df.empty or not all(c in df.columns for c in ['open', 'close', 'high', 'low']):
            return {}
        
        patterns_found = {}
        
        try:
            # Engulfing patterns
            patterns_found.update(self._detect_engulfing_patterns(df, target_column))
            
            # Doji patterns
            patterns_found.update(self._detect_doji_patterns(df, target_column))
            
            # Inside bar patterns
            patterns_found.update(self._detect_inside_bar_patterns(df, target_column))
            
            # Three bar patterns
            patterns_found.update(self._detect_three_bar_patterns(df, target_column))
            
            # Star patterns
            patterns_found.update(self._detect_star_patterns(df, target_column))
            
            with self._lock:
                self.patterns.update(patterns_found)
            
            logger.info(f"Discovered {len(patterns_found)} candlestick patterns")
            return patterns_found
        
        except Exception as e:
            logger.error(f"Error in candlestick pattern detection: {e}")
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
            
            # Bullish engulfing
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
            
            # Bearish engulfing
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
        
        except Exception as e:
            logger.warning(f"Error in engulfing pattern detection: {e}")
        
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
        
        except Exception as e:
            logger.warning(f"Error in doji pattern detection: {e}")
        
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
        
        except Exception as e:
            logger.warning(f"Error in inside bar pattern detection: {e}")
        
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
            
            # Three white soldiers
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
            
            # Three black crows
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
        
        except Exception as e:
            logger.warning(f"Error in three bar pattern detection: {e}")
        
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
            
            # Morning star
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
            
            # Evening star
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
        
        except Exception as e:
            logger.warning(f"Error in star pattern detection: {e}")
        
        return patterns
    
    def _calculate_pattern_metrics(
        self,
        pattern_signal: pd.Series,
        returns: pd.Series
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a pattern"""
        pattern_returns = returns[pattern_signal].dropna()
        
        if len(pattern_returns) == 0:
            return {
                'occurrence_count': 0,
                'success_rate': 0.0,
                'avg_profit': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'reliability': 0.0,
                'lookback_periods': len(returns)
            }
        
        occurrences = pattern_signal.sum()
        wins = (pattern_returns > 0).sum()
        losses = (pattern_returns < 0).sum()
        
        success_rate = wins / occurrences if occurrences > 0 else 0.0
        avg_profit = pattern_returns[pattern_returns > 0].mean() if wins > 0 else 0.0
        avg_loss = abs(pattern_returns[pattern_returns < 0].mean()) if losses > 0 else 0.0
        
        profit_factor = avg_profit / (avg_loss + 1e-10) if avg_loss > 0 else 1.0 if avg_profit > 0 else 0.0
        reliability = min(1.0, occurrences / len(returns)) if len(returns) > 0 else 0.0
        
        return {
            'occurrence_count': int(occurrences),
            'success_rate': max(0.0, min(success_rate, 1.0)),
            'avg_profit': float(avg_profit),
            'avg_loss': float(avg_loss),
            'profit_factor': max(0.0, profit_factor),
            'reliability': max(0.0, min(reliability, 1.0)),
            'lookback_periods': len(returns)
        }
    
    # ==================== COMBINATION DISCOVERY ====================
    
    def analyze_combination(
        self,
        df: pd.DataFrame,
        indicator_names: List[str],
        target_column: str = "returns",
        combination_rule: str = "average"
    ) -> Optional[IndicatorCombination]:
        """Analyze combination of indicators"""
        
        if not indicator_names or not all(name in df.columns for name in indicator_names):
            return None
        
        if target_column not in df.columns:
            return None
        
        try:
            df_work = df[indicator_names + [target_column]].dropna()
            
            if len(df_work) < self.min_samples:
                return None
            
            if combination_rule == "average":
                combined_signal = df_work[indicator_names].mean(axis=1).values
            elif combination_rule == "weighted":
                weights = np.array([self.indicators[n].composite_score() if n in self.indicators else 0.5 
                                   for n in indicator_names])
                weights = weights / (weights.sum() + 1e-10)
                combined_signal = (df_work[indicator_names].values * weights).sum(axis=1)
            else:
                combined_signal = df_work[indicator_names].mean(axis=1).values
            
            returns = df_work[target_column].values
            
            win_rate = self._calculate_win_rate(combined_signal, returns)
            profit_factor = self._calculate_profit_factor(combined_signal, returns)
            sharpe_ratio = self._calculate_sharpe_ratio(combined_signal, returns)
            signal_quality = self._calculate_signal_quality(combined_signal, returns)
            
            synergy_factor = self._calculate_synergy(indicator_names, combined_signal, returns)
            
            combined_score = (
                win_rate * 0.3 +
                min(profit_factor / 2.0, 1.0) * 0.3 +
                max(min(sharpe_ratio / 3.0, 1.0), 0.0) * 0.2 +
                signal_quality * 0.2
            )
            
            combination = IndicatorCombination(
                indicators=indicator_names,
                combined_score=combined_score,
                win_rate=max(0.0, min(win_rate, 1.0)),
                profit_factor=max(0.0, profit_factor),
                sharpe_ratio=sharpe_ratio,
                synergy_factor=synergy_factor,
                signal_quality=max(0.0, min(signal_quality, 1.0)),
                backtest_periods=len(df_work),
                discovered_at=datetime.now(timezone.utc),
                metadata={
                    "combination_rule": combination_rule,
                    "num_indicators": len(indicator_names),
                    "data_points": len(df_work)
                }
            )
            
            comb_key = "_".join(sorted(indicator_names))
            with self._lock:
                self.combinations[comb_key] = combination
            
            logger.info(f"Analyzed combination {indicator_names}: score={combination.effective_score():.4f}")
            return combination
        
        except Exception as e:
            logger.error(f"Error analyzing combination {indicator_names}: {e}")
            return None
    
    def discover_combinations(
        self,
        df: pd.DataFrame,
        max_combination_size: int = 3,
        target_column: str = "returns",
        min_combo_score: float = 0.55,
        combination_rule: str = "weighted"
    ) -> Dict[str, IndicatorCombination]:
        """Discover optimal indicator combinations"""
        
        available_indicators = [n for n in self.indicators.keys() if n in df.columns]
        
        if not available_indicators:
            logger.warning("No analyzed indicators available")
            return {}
        
        discovered_combos = {}
        
        for size in range(2, min(max_combination_size + 1, len(available_indicators) + 1)):
            for combo in combinations(available_indicators, size):
                combo_list = list(combo)
                combination = self.analyze_combination(df, combo_list, target_column, combination_rule)
                
                if combination and combination.effective_score() >= min_combo_score:
                    comb_key = "_".join(sorted(combo_list))
                    discovered_combos[comb_key] = combination
        
        logger.info(f"Discovered {len(discovered_combos)} combinations with score >= {min_combo_score}")
        return discovered_combos
    
    # ==================== RANKING & EXPORT ====================
    
    def get_top_indicators(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top-ranked indicators"""
        sorted_indicators = sorted(
            self.indicators.values(),
            key=lambda x: x.composite_score(),
            reverse=True
        )
        return [ind.to_dict() for ind in sorted_indicators[:top_n]]
    
    def get_top_patterns(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top-ranked patterns"""
        sorted_patterns = sorted(
            self.patterns.values(),
            key=lambda x: x.score(),
            reverse=True
        )
        return [pat.to_dict() for pat in sorted_patterns[:top_n]]
    
    def get_top_combinations(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top-ranked indicator combinations"""
        sorted_combos = sorted(
            self.combinations.values(),
            key=lambda x: x.effective_score(),
            reverse=True
        )
        return [combo.to_dict() for combo in sorted_combos[:top_n]]
    
    def export_discoveries(self, output_path: Path) -> None:
        """Export all discoveries to JSON file"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "indicators": {name: metric.to_dict() for name, metric in self.indicators.items()},
                "patterns": {name: pattern.to_dict() for name, pattern in self.patterns.items()},
                "combinations": {name: combo.to_dict() for name, combo in self.combinations.items()},
                "top_indicators": self.get_top_indicators(20),
                "top_patterns": self.get_top_patterns(20),
                "top_combinations": self.get_top_combinations(20),
                "statistics": {
                    "total_indicators": len(self.indicators),
                    "total_patterns": len(self.patterns),
                    "total_combinations": len(self.combinations),
                    "best_indicator_score": max([m.composite_score() for m in self.indicators.values()], default=0),
                    "best_pattern_score": max([p.score() for p in self.patterns.values()], default=0),
                    "best_combination_score": max([c.effective_score() for c in self.combinations.values()], default=0)
                }
            }
            
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Discoveries exported to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting discoveries: {e}")
    
    # ==================== HELPER METHODS ====================
    
    def _calculate_win_rate(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate win rate based on signal and returns"""
        if len(signal) < 2:
            return 0.5
        
        signal_direction = np.sign(np.diff(signal))
        returns_direction = np.sign(returns[1:])
        
        matches = np.sum(signal_direction == returns_direction)
        return matches / len(signal_direction) if len(signal_direction) > 0 else 0.5
    
    def _calculate_profit_factor(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate profit factor"""
        if len(signal) < 2:
            return 1.0
        
        weighted_returns = returns[1:] * np.sign(np.diff(signal))
        gains = np.sum(weighted_returns[weighted_returns > 0])
        losses = np.abs(np.sum(weighted_returns[weighted_returns < 0]))
        
        if losses == 0:
            return 2.0 if gains > 0 else 1.0
        return gains / losses if gains > 0 else 0.1
    
    def _calculate_sharpe_ratio(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        return (mean_return / std_return) * np.sqrt(252)
    
    def _calculate_max_drawdown(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return float(np.min(drawdown))
    
    def _calculate_accuracy(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate prediction accuracy"""
        if len(signal) < 2:
            return 0.5
        
        signal_binary = (np.diff(signal) > 0).astype(int)
        returns_binary = (returns[1:] > 0).astype(int)
        
        correct = np.sum(signal_binary == returns_binary)
        return correct / len(signal_binary) if len(signal_binary) > 0 else 0.5
    
    def _calculate_precision_recall_f1(self, signal: np.ndarray, returns: np.ndarray) -> Tuple[float, float, float]:
        """Calculate precision, recall, F1"""
        if len(signal) < 2:
            return 0.5, 0.5, 0.5
        
        signal_binary = (np.diff(signal) > 0).astype(int)
        returns_binary = (returns[1:] > 0).astype(int)
        
        tp = np.sum((signal_binary == 1) & (returns_binary == 1))
        fp = np.sum((signal_binary == 1) & (returns_binary == 0))
        fn = np.sum((signal_binary == 0) & (returns_binary == 1))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return precision, recall, f1
    
    def _calculate_signal_quality(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate overall signal quality"""
        if len(signal) < 2:
            return 0.0
        
        _, _, f1 = self._calculate_precision_recall_f1(signal, returns)
        win_rate = self._calculate_win_rate(signal, returns)
        
        return (f1 * 0.5 + win_rate * 0.5)
    
    def _calculate_synergy(self, indicators: List[str], combined_signal: np.ndarray, returns: np.ndarray) -> float:
        """Calculate synergy factor between indicators"""
        if len(indicators) < 2:
            return 1.0
        
        try:
            individual_scores = [
                self.indicators[name].composite_score() if name in self.indicators else 0.5
                for name in indicators
            ]
            avg_individual = np.mean(individual_scores)
            
            combined_accuracy = self._calculate_accuracy(combined_signal, returns)
            
            synergy = combined_accuracy / (avg_individual + 1e-10)
            return min(2.0, max(0.5, synergy))
        except:
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
    'IndicatorMetric',
    'PatternMetric',
    'IndicatorCombination',
    'IndicatorCategory',
    'PatternType',
]
