#!/usr/bin/env python3
"""
Stress-test discovery pipeline.
Runs discovery many times to surface race conditions, memory leaks, and crashes.
Usage:
  python stress_discovery.py [--runs 100] [--data data/eurusd_1h_synthetic.parquet]
"""
import argparse
import sys
import time
import traceback
import logging
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Quiet logs during stress
logging.disable(logging.INFO)

from trading_ai_system import data, features, discovery


def run_once(df_raw: pd.DataFrame, run_id: int, min_samples: int = 50) -> dict:
    t0 = time.perf_counter()
    df = data.clean_ohlcv_data(df_raw.copy())
    if "volume" not in df.columns:
        df["volume"] = 0.0
    df_feat, _ = features.engineer_features_for_timeframe(
        df, timeframe="1h", compute_advanced=True, use_discovery=False, use_cache=False
    )
    cfg = discovery.DiscoveryConfig(
        min_samples=min_samples,
        parallel_enabled=True,
        n_workers=1,
        caching_enabled=False,
    )
    disc = discovery.Discovery(config=cfg)
    found = disc.discover_indicators(df_feat, target_column="return_1bar", min_score=0.45)
    combos = {}
    if found:
        top_names = list(found.keys())[:6]
        disc.indicators = {k: v for k, v in disc.indicators.items() if k in top_names}
        combos = disc.discover_combinations(
            df_feat, target_column="return_1bar", max_combination_size=2, min_score=0.5
        )
    elapsed = time.perf_counter() - t0
    return {
        "run": run_id,
        "indicators": len(found),
        "combinations": len(combos),
        "features": len(df_feat.columns),
        "elapsed": elapsed,
        "ok": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--data", type=str, default="data/eurusd_1h_synthetic.parquet")
    parser.add_argument("--min-samples", type=int, default=50)
    args = parser.parse_args()

    path = Path(args.data)
    if not path.exists():
        print(f"Data not found: {path}")
        sys.exit(1)

    print(f"Loading {path} ...")
    df_raw = data.DataLoader().load_parquet(path)
    if "symbol" in df_raw.columns:
        df_raw = df_raw[df_raw["symbol"].astype(str).str.upper() == "EURUSD"]
    if "timeframe" in df_raw.columns:
        df_raw = df_raw[df_raw["timeframe"].astype(str).str.lower().isin(["1h", "h1"])]
    print(f"Rows: {len(df_raw):,}")

    successes = 0
    failures = 0
    total_time = 0.0
    errors = []

    for i in range(1, args.runs + 1):
        try:
            res = run_once(df_raw, i, min_samples=args.min_samples)
            successes += 1
            total_time += res["elapsed"]
            if i % 10 == 0 or i == 1:
                print(
                    f"[{i:4d}/{args.runs}] ok  indicators={res['indicators']:2d} "
                    f"combos={res['combinations']:2d} features={res['features']:3d} "
                    f"time={res['elapsed']:.3f}s"
                )
        except Exception as e:
            failures += 1
            err = f"Run {i}: {type(e).__name__}: {e}"
            errors.append(err)
            print(f"[{i:4d}/{args.runs}] FAIL {err}")
            if failures <= 3:
                traceback.print_exc()

    print("=" * 60)
    print(f"Runs: {args.runs}  Success: {successes}  Fail: {failures}")
    if successes:
        print(f"Avg time: {total_time / successes:.3f}s")
    if errors:
        print("Sample errors:")
        for e in errors[:5]:
            print(" ", e)
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
