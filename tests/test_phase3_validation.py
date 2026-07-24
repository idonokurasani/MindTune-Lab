"""Validation tests for Phase 3 independent validation modules."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from hebrew.phase3.adversarial import run_adversarial_tests
from hebrew.phase3.benchmark import build_benchmark_partitions, load_benchmark_partitions
from hebrew.phase3.data_loader import Phase3DataLoader
from hebrew.phase3.differential import run_differential_analysis
from hebrew.phase3.round_trip import run_round_trip_tests


@pytest.fixture(scope="module")
def loader() -> Phase3DataLoader:
    """Shared loaded Phase 3 data."""
    ld = Phase3DataLoader()
    ld.load_all()
    return ld


def test_differential_analysis(loader: Phase3DataLoader) -> None:
    result = run_differential_analysis(loader)
    assert "eran_count" in result
    assert "inflector_count" in result
    assert "agreement_count" in result
    assert "disagreement_count" in result
    assert "sample_disagreements" in result
    assert result["eran_count"] > 0
    assert result["inflector_count"] > 0
    # The two sources are expected to be identical.
    assert result["agreement_count"] > 0


def test_round_trip_tests(loader: Phase3DataLoader) -> None:
    result = run_round_trip_tests(loader, sample_size=50)
    assert "total_available" in result
    assert "sample_size" in result
    assert "successes" in result
    assert "failures" in result
    assert "by_binyan" in result
    assert "by_form_key" in result
    assert result["sample_size"] > 0


def test_adversarial_tests(loader: Phase3DataLoader) -> None:
    result = run_adversarial_tests(loader, sample_size=20)
    assert "mutation_types" in result
    assert "mutation_counts" in result
    assert "total_mutations" in result
    assert "false_acceptance_count" in result
    assert "false_acceptance_by_type" in result
    assert result["total_mutations"] > 0


def test_benchmark_partitions(loader: Phase3DataLoader) -> None:
    result = build_benchmark_partitions(
        loader,
        seed=42,
        dev_ratio=0.1,
        calibration_ratio=0.2,
    )
    assert "path" in result
    assert "total_records" in result
    assert "partition_counts" in result
    assert "leakage_detected" in result
    assert "leakage_count" in result

    assert not result["leakage_detected"]
    assert result["leakage_count"] == 0
    assert result["total_records"] > 0

    total_from_counts = sum(result["partition_counts"].values())
    assert total_from_counts == result["total_records"]

    path = Path(result["path"])
    assert path.exists()

    records = load_benchmark_partitions(path)
    assert len(records) == result["total_records"]

    required_keys = {
        "infinitive",
        "form_key",
        "surface_vocalized",
        "surface_plain",
        "root",
        "binyan",
        "partition",
        "source",
    }
    for rec in records[:100]:
        assert required_keys <= set(rec)

    # Leakage check: no (surface, form_key) pair may appear in >1 partition.
    pair_to_partition: dict[tuple[str, str], str] = {}
    for rec in records:
        pair = (rec["surface_vocalized"], rec["form_key"])
        part = rec["partition"]
        if pair in pair_to_partition:
            assert pair_to_partition[pair] == part, f"leakage for pair {pair}: {part} vs {pair_to_partition[pair]}"
        else:
            pair_to_partition[pair] = part

    # Partition names must be one of the three expected values.
    expected_partitions = {"development", "calibration", "blind_evaluation"}
    for rec in records:
        assert rec["partition"] in expected_partitions


def test_ci_regression_gates(loader: Phase3DataLoader) -> None:
    """High-level regression gates for the Phase 3 validation pipeline."""
    # Round-trip: morphology tags should map back to a generated surface.
    round_trip = run_round_trip_tests(loader, sample_size=200)
    assert round_trip["sample_size"] > 0
    success_rate = round_trip["successes"] / round_trip["sample_size"]
    assert success_rate >= 0.99, f"round-trip success rate {success_rate} below gate"

    # Adversarial: mutated surfaces should rarely be found in the corpus.
    adversarial = run_adversarial_tests(loader, sample_size=50)
    assert adversarial["total_mutations"] > 0
    far = adversarial["false_acceptance_rate"]
    assert far <= 0.10, f"adversarial false-acceptance rate {far} above gate"

    # Differential: Eran Tomer and the fresh Verb Inflector must not diverge.
    differential = run_differential_analysis(loader)
    assert differential["disagreement_count"] == 0

    # 100-verb expansion must produce a meaningful number of verified records.
    repo_root = Path(__file__).resolve().parents[1]
    gold_path = repo_root / "data" / "hebrew" / "phase3" / "automatic_gold_100.json"
    with gold_path.open("r", encoding="utf-8") as f:
        gold = json.load(f)
    summary = gold["status_summary"]
    accepted = summary.get("verified_consensus", 0) + summary.get("high_confidence_candidate", 0)
    total = sum(summary.values())
    assert total > 0
    assert accepted / total >= 0.80, f"accepted proportion {accepted/total} below gate"
