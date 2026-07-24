#!/usr/bin/env bash
# Phase 3 CI regression gate.
# Runs the full validation test suite and reports key metrics.
set -euo pipefail

cd "$(dirname "$0")/.."

source .venv_phonikud/bin/activate

echo "Running Phase 3 tests..."
python -m pytest tests/ -q

echo ""
echo "Running validation metrics..."
python - <<'PY'
import json
from pathlib import Path

from hebrew.phase3.adversarial import run_adversarial_tests
from hebrew.phase3.benchmark import build_benchmark_partitions
from hebrew.phase3.data_loader import Phase3DataLoader
from hebrew.phase3.differential import run_differential_analysis
from hebrew.phase3.round_trip import run_round_trip_tests

loader = Phase3DataLoader()
loader.load_all()

rt = run_round_trip_tests(loader, sample_size=1000)
ad = run_adversarial_tests(loader, sample_size=100)
diff = run_differential_analysis(loader)
bench = build_benchmark_partitions(loader, seed=42)

gold_path = Path("data/hebrew/phase3/automatic_gold_100.json")
with gold_path.open("r", encoding="utf-8") as f:
    gold = json.load(f)

print(f"round_trip_success_rate: {rt['successes'] / rt['sample_size']:.4f}")
print(f"adversarial_false_acceptance_rate: {ad['false_acceptance_rate']:.4f}")
print(f"differential_disagreements: {diff['disagreement_count']}")
print(f"benchmark_records: {bench['total_records']}")
print(f"benchmark_leakage: {bench['leakage_count']}")
print(f"automatic_gold_status_summary: {gold['status_summary']}")
PY

echo ""
echo "Phase 3 CI gate passed."
