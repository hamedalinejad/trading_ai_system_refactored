#!/bin/bash
# Quick discovery runner for CPU laptop + multi-TF parquet
# Usage:
#   ./run_discovery.sh /path/to/5year_data.parquet EURUSD 1h 20

set -e

DATA_FILE="${1:-data/sample_eurusd_multi_tf.parquet}"
PAIR="${2:-EURUSD}"
TF="${3:-1h}"
TOP="${4:-15}"

echo "=============================================="
echo " Trading AI System - Strategy Discovery"
echo " Pair      : $PAIR"
echo " Timeframe : $TF"
echo " Data      : $DATA_FILE"
echo "=============================================="

python main.py discovery \
  -p "$PAIR" \
  -d "$DATA_FILE" \
  --timeframe "$TF" \
  --top "$TOP" \
  --workers 2 \
  --min-samples 100

echo ""
echo "Results saved under outputs/"
