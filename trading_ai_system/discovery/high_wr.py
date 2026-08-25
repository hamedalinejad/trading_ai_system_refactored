"""
High Win-Rate Rule Discovery
Searches discrete entry rules that maximize realized trade win-rate.

IMPORTANT REALITY CHECK:
- True 100% win-rate on out-of-sample forex data with realistic spread/slippage
  is not achievable in a robust, repeatable way.
- This module finds rules that *appear* extremely high-WR on the given sample
  (including 100% when trade count is low / overfit). Always validate OOS.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from itertools import product

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class HighWRRule:
    """A discrete trading rule with measured win-rate."""
    name: str
    direction: str  # "long" or "short"
    conditions: List[str]
    win_rate: float
    n_trades: int
    avg_return: float
    total_return: float
    profit_factor: float
    max_drawdown: float
    precision: float
    oos_win_rate: float = 0.0
    oos_n_trades: int = 0
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


def _apply_cost(returns: np.ndarray, cost_per_side: float = 0.0001) -> np.ndarray:
    """Subtract round-trip cost approximation from trade returns."""
    # cost applied once per trade return
    return returns - (2.0 * cost_per_side)


def evaluate_signal(
    signal: np.ndarray,
    forward_returns: np.ndarray,
    cost_per_side: float = 0.0001,
) -> Dict[str, float]:
    """
    Evaluate a binary signal (1 = take trade, 0 = skip).
    forward_returns already signed for direction (positive = win for that side).
    """
    mask = signal.astype(bool)
    n = int(mask.sum())
    if n == 0:
        return {
            "win_rate": 0.0,
            "n_trades": 0,
            "avg_return": 0.0,
            "total_return": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
            "precision": 0.0,
        }

    r = _apply_cost(forward_returns[mask], cost_per_side)
    wins = r > 0
    wr = float(wins.mean())
    gains = r[r > 0].sum()
    losses = -r[r < 0].sum()
    pf = float(gains / (losses + 1e-12)) if losses > 0 else (2.0 if gains > 0 else 0.0)

    # equity curve drawdown on trade sequence
    equity = np.cumsum(r)
    peak = np.maximum.accumulate(equity)
    dd = equity - peak
    max_dd = float(dd.min()) if len(dd) else 0.0

    return {
        "win_rate": wr,
        "n_trades": n,
        "avg_return": float(r.mean()),
        "total_return": float(r.sum()),
        "profit_factor": pf,
        "max_drawdown": max_dd,
        "precision": wr,  # for directional binary, same as WR
    }


def build_threshold_candidates(
    series: pd.Series,
    quantiles: Tuple[float, ...] = (0.1, 0.2, 0.3, 0.7, 0.8, 0.9),
) -> List[Tuple[str, pd.Series]]:
    """Generate threshold boolean series for one feature."""
    out = []
    vals = series.replace([np.inf, -np.inf], np.nan).dropna()
    if len(vals) < 50:
        return out
    for q in quantiles:
        thr = float(vals.quantile(q))
        out.append((f"{series.name}>={thr:.6g}", series >= thr))
        out.append((f"{series.name}<={thr:.6g}", series <= thr))
    # also median cross style
    med = float(vals.median())
    out.append((f"{series.name}>{med:.6g}", series > med))
    out.append((f"{series.name}<{med:.6g}", series < med))
    return out


def discover_high_wr_rules(
    df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    horizon: int = 1,
    min_trades: int = 30,
    min_win_rate: float = 0.70,
    max_conditions: int = 2,
    cost_per_side: float = 0.0001,
    oos_ratio: float = 0.3,
    top_k: int = 30,
) -> List[HighWRRule]:
    """
    Brute-force / combinatorial search for high win-rate discrete rules.

    - Uses next `horizon` bar return as outcome.
    - Splits last oos_ratio for out-of-sample check.
    - Searches single and pairwise threshold conditions.
    """
    if "close" not in df.columns:
        raise ValueError("df must contain 'close'")

    work = df.copy()
    # forward return (raw, direction applied later)
    work["fwd_ret"] = work["close"].pct_change(horizon).shift(-horizon)
    work = work.dropna(subset=["fwd_ret"]).reset_index(drop=True)

    n = len(work)
    split = int(n * (1.0 - oos_ratio))
    if split < min_trades * 2:
        split = max(int(n * 0.7), min_trades * 2)

    is_df = work.iloc[:split]
    oos_df = work.iloc[split:]

    exclude = {
        "open", "high", "low", "close", "volume", "spread", "timestamp",
        "is_market_open", "fwd_ret", "return_1bar", "return_5bar", "return_20bar",
        "log_return_1bar", "acceleration", "jerk", "price_velocity",
    }
    if feature_cols is None:
        numeric = work.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in numeric if c not in exclude]

    # limit features for CPU
    feature_cols = feature_cols[:25]

    # Precompute candidate masks per feature (on full work, then slice)
    candidates: List[Tuple[str, np.ndarray]] = []
    for col in feature_cols:
        if col not in work.columns:
            continue
        for name, mask_s in build_threshold_candidates(work[col]):
            candidates.append((name, mask_s.fillna(False).astype(bool).values))

    logger.info(
        f"High-WR search: {len(candidates)} base conditions, "
        f"IS={len(is_df)}, OOS={len(oos_df)}, horizon={horizon}"
    )

    rules: List[HighWRRule] = []
    fwd_is = is_df["fwd_ret"].values
    fwd_oos = oos_df["fwd_ret"].values if len(oos_df) else np.array([])

    def score_rule(wr, n_trades, pf, oos_wr, oos_n):
        # Prefer high WR + enough trades + OOS confirmation
        trade_factor = min(n_trades / 100.0, 1.0)
        oos_bonus = 0.0
        if oos_n >= max(10, min_trades // 3):
            oos_bonus = 0.35 * oos_wr
        return 0.45 * wr + 0.20 * min(pf / 3.0, 1.0) + 0.20 * trade_factor + oos_bonus

    # --- single conditions ---
    for name, full_mask in candidates:
        sig_is = full_mask[:split]
        # Long
        metrics = evaluate_signal(sig_is, fwd_is, cost_per_side)
        if metrics["n_trades"] >= min_trades and metrics["win_rate"] >= min_win_rate:
            oos_m = {"win_rate": 0.0, "n_trades": 0}
            if len(fwd_oos):
                oos_m = evaluate_signal(full_mask[split:], fwd_oos, cost_per_side)
            rule = HighWRRule(
                name=f"LONG|{name}",
                direction="long",
                conditions=[name],
                win_rate=metrics["win_rate"],
                n_trades=metrics["n_trades"],
                avg_return=metrics["avg_return"],
                total_return=metrics["total_return"],
                profit_factor=metrics["profit_factor"],
                max_drawdown=metrics["max_drawdown"],
                precision=metrics["precision"],
                oos_win_rate=oos_m["win_rate"],
                oos_n_trades=oos_m["n_trades"],
                score=score_rule(
                    metrics["win_rate"], metrics["n_trades"], metrics["profit_factor"],
                    oos_m["win_rate"], oos_m["n_trades"],
                ),
            )
            rules.append(rule)

        # Short (invert forward return)
        metrics = evaluate_signal(sig_is, -fwd_is, cost_per_side)
        if metrics["n_trades"] >= min_trades and metrics["win_rate"] >= min_win_rate:
            oos_m = {"win_rate": 0.0, "n_trades": 0}
            if len(fwd_oos):
                oos_m = evaluate_signal(full_mask[split:], -fwd_oos, cost_per_side)
            rule = HighWRRule(
                name=f"SHORT|{name}",
                direction="short",
                conditions=[name],
                win_rate=metrics["win_rate"],
                n_trades=metrics["n_trades"],
                avg_return=metrics["avg_return"],
                total_return=metrics["total_return"],
                profit_factor=metrics["profit_factor"],
                max_drawdown=metrics["max_drawdown"],
                precision=metrics["precision"],
                oos_win_rate=oos_m["win_rate"],
                oos_n_trades=oos_m["n_trades"],
                score=score_rule(
                    metrics["win_rate"], metrics["n_trades"], metrics["profit_factor"],
                    oos_m["win_rate"], oos_m["n_trades"],
                ),
            )
            rules.append(rule)

    # --- pairwise AND conditions (limited) ---
    if max_conditions >= 2 and len(candidates) > 1:
        # take top features by variance to limit combos
        ranked = sorted(
            candidates,
            key=lambda x: float(np.std(x[1].astype(float))) if x[1].any() else 0.0,
            reverse=True,
        )[:40]
        for (n1, m1), (n2, m2) in product(ranked, repeat=2):
            if n1 >= n2:
                continue
            full_mask = m1 & m2
            sig_is = full_mask[:split]
            n_is = int(sig_is.sum())
            if n_is < min_trades:
                continue

            for direction, sign in (("long", 1.0), ("short", -1.0)):
                metrics = evaluate_signal(sig_is, sign * fwd_is, cost_per_side)
                if metrics["n_trades"] < min_trades or metrics["win_rate"] < min_win_rate:
                    continue
                oos_m = {"win_rate": 0.0, "n_trades": 0}
                if len(fwd_oos):
                    oos_m = evaluate_signal(full_mask[split:], sign * fwd_oos, cost_per_side)
                rule = HighWRRule(
                    name=f"{direction.upper()}|{n1}&{n2}",
                    direction=direction,
                    conditions=[n1, n2],
                    win_rate=metrics["win_rate"],
                    n_trades=metrics["n_trades"],
                    avg_return=metrics["avg_return"],
                    total_return=metrics["total_return"],
                    profit_factor=metrics["profit_factor"],
                    max_drawdown=metrics["max_drawdown"],
                    precision=metrics["precision"],
                    oos_win_rate=oos_m["win_rate"],
                    oos_n_trades=oos_m["n_trades"],
                    score=score_rule(
                        metrics["win_rate"], metrics["n_trades"], metrics["profit_factor"],
                        oos_m["win_rate"], oos_m["n_trades"],
                    ),
                )
                rules.append(rule)

    rules.sort(key=lambda r: (r.win_rate, r.score, r.n_trades), reverse=True)

    # Deduplicate near-identical
    seen = set()
    unique: List[HighWRRule] = []
    for r in rules:
        key = (r.direction, tuple(sorted(r.conditions)), round(r.win_rate, 4))
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
        if len(unique) >= top_k:
            break

    logger.info(f"High-WR discovery found {len(unique)} rules (min_WR={min_win_rate}, min_trades={min_trades})")
    return unique


def find_perfect_wr_rules(
    df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    horizon: int = 1,
    min_trades: int = 10,
    cost_per_side: float = 0.0001,
    oos_ratio: float = 0.3,
    top_k: int = 20,
) -> List[HighWRRule]:
    """
    Specifically hunt for rules with win_rate == 1.0 on in-sample.
    These are almost always overfit / rare; OOS stats are critical.
    """
    rules = discover_high_wr_rules(
        df,
        feature_cols=feature_cols,
        horizon=horizon,
        min_trades=min_trades,
        min_win_rate=0.999,  # effectively 100%
        max_conditions=2,
        cost_per_side=cost_per_side,
        oos_ratio=oos_ratio,
        top_k=top_k * 3,
    )
    perfect = [r for r in rules if r.win_rate >= 0.999]
    perfect.sort(key=lambda r: (r.oos_win_rate, r.n_trades), reverse=True)
    return perfect[:top_k]
