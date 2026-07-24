"""Build frozen benchmark partitions for Phase 3.

Partitions are kept strictly separated by unique row signature (pattern,
table_number, base_form, morphology) so that no exact form used for rule
building appears in calibration or blind evaluation.  Vocalized surfaces come
from the external Eran Tomer / Verb Inflector CSV.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from ..morphology import binyan_from_pattern, morphology_features_to_form_key, parse_morphology_tag
from ..normalization import normalize_hebrew, standard_unvocalized, strip_niqqud
from .data_loader import Phase3DataLoader
from .selection import select_100_verbs


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_output_path() -> Path:
    return _repo_root() / "data" / "hebrew" / "phase3" / "benchmark_partitions.json"


def _group_infinitive(rows: list[dict[str, str]]) -> str:
    for row in rows:
        if row["morphology"].startswith("INFINITIVE"):
            return row["vocalized_inflection"]
    if rows:
        return rows[0]["vocalized_inflection"]
    return ""


def _row_signature(pattern: str, table_number: int, base_form: str, morphology: str) -> str:
    return f"{pattern}::{table_number}::{base_form}::{morphology}"


def _partition_by_signature(signature: str, ratios: dict[str, float], seed: int = 42) -> str:
    h = int(hashlib.md5(signature.encode(), usedforsecurity=False).hexdigest(), 16)
    rng = random.Random(h ^ seed)
    value = rng.random()
    cumulative = 0.0
    for part, ratio in ratios.items():
        cumulative += ratio
        if value < cumulative:
            return part
    return list(ratios.keys())[-1]


def build_benchmark_partitions(
    loader: Phase3DataLoader | None = None,
    seed: int = 42,
    dev_ratio: float = 0.10,
    calibration_ratio: float = 0.20,
    use_100_verbs_as_blind: bool = True,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build and save development, calibration and blind evaluation partitions.

    Uses the 100-verb selection as a coverage stratum.  If *use_100_verbs_as_blind*
    is True, all rows from the selected 100 verb groups are reserved for the blind
    partition; the remaining rows are split into development/calibration/blind by
    deterministic hash.
    """
    if loader is None:
        loader = Phase3DataLoader()
        loader.load_all()

    selected_verbs = select_100_verbs(loader)
    selected_group_keys = {
        (v["pattern"], v["table_number"], v["base_form_plain"]) for v in selected_verbs
    }

    groups = loader.verb_groups()
    ratios = {"development": dev_ratio, "calibration": calibration_ratio}
    ratios["blind_evaluation"] = 1.0 - dev_ratio - calibration_ratio

    group_meta: dict[tuple[str, int, str], dict[str, Any]] = {}
    for key, rows in groups.items():
        group_meta[key] = {
            "infinitive": _group_infinitive(rows),
            "root": loader.get_root(*key),
            "binyan": binyan_from_pattern(key[0]),
            "selected_100": key in selected_group_keys,
        }

    # Group by (surface_vocalized, form_key) so the same pair never appears in
    # more than one partition.  Each pair may come from multiple verb groups
    # (true homographs); we keep the first contributing group as the primary
    # reference and record any ambiguity.
    seen: set[str] = set()
    pair_info: dict[tuple[str, str], dict[str, Any]] = {}
    duplicate_count = 0

    for key, rows in groups.items():
        meta = group_meta[key]
        pattern, table_number, base_form = key
        for row in rows:
            surface_vocalized = normalize_hebrew(row["vocalized_inflection"])
            surface_plain = standard_unvocalized(surface_vocalized)
            features = parse_morphology_tag(row["morphology"], pattern, table_number)
            form_key = morphology_features_to_form_key(features)
            signature = _row_signature(pattern, table_number, base_form, row["morphology"])

            if signature in seen:
                duplicate_count += 1
                continue
            seen.add(signature)

            pair = (surface_vocalized, form_key)
            if pair not in pair_info:
                pair_info[pair] = {
                    "surface_vocalized": surface_vocalized,
                    "surface_plain": surface_plain,
                    "form_key": form_key,
                    "primary_meta": meta,
                    "primary_group_key": f"{pattern}_{table_number}_{base_form}",
                    "primary_signature": signature,
                    "group_keys": [f"{pattern}_{table_number}_{base_form}"],
                    "signatures": [signature],
                    "selected_100": meta["selected_100"],
                    "ambiguous": False,
                }
            else:
                info = pair_info[pair]
                info["group_keys"].append(f"{pattern}_{table_number}_{base_form}")
                info["signatures"].append(signature)
                if info["group_keys"][-1] != info["group_keys"][-2]:
                    info["ambiguous"] = True
                if meta["selected_100"]:
                    info["selected_100"] = True

    records: list[dict[str, Any]] = []
    leakage: list[dict[str, str]] = []

    for info in pair_info.values():
        meta = info["primary_meta"]
        pair_signature = f"{info['surface_vocalized']}::{info['form_key']}"

        if use_100_verbs_as_blind and info["selected_100"]:
            partition = "blind_evaluation"
        else:
            partition = _partition_by_signature(pair_signature, ratios, seed=seed)

        records.append(
            {
                "record_id": pair_signature,
                "partition": partition,
                "group_key": info["primary_group_key"],
                "group_keys": info["group_keys"],
                "infinitive": meta["infinitive"],
                "form_key": info["form_key"],
                "surface_vocalized": info["surface_vocalized"],
                "surface_plain": info["surface_plain"],
                "root": meta["root"],
                "binyan": meta["binyan"],
                "selected_100": info["selected_100"],
                "ambiguous": info["ambiguous"],
                "source": "eran_tomer",
                "reference_status": "accepted",
            }
        )

    # Cross-partition leakage check by pair signature.
    partition_sets: dict[str, set[str]] = {"development": set(), "calibration": set(), "blind_evaluation": set()}
    for rec in records:
        partition_sets[rec["partition"]].add(rec["record_id"])
    for a, set_a in partition_sets.items():
        for b, set_b in partition_sets.items():
            if a >= b:
                continue
            cross = set_a & set_b
            for sig in cross:
                leakage.append({"type": "cross_partition", "partitions": f"{a},{b}", "signature": sig})

    partition_counts = {p: sum(1 for r in records if r["partition"] == p) for p in ratios}
    selected_100_records = sum(1 for r in records if r["selected_100"])

    if output_path is None:
        output_path = _default_output_path()
    else:
        output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "source": "frozen_external_eran_tomer",
                "description": "Benchmark partitions built from external Verb Inflector / Eran Tomer CSV.",
                "seed": seed,
                "ratios": ratios,
                "record_count": len(records),
                "partition_counts": partition_counts,
                "selected_100_records": selected_100_records,
                "leakage": leakage,
                "records": records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "path": str(output_path),
        "total_records": len(records),
        "partition_counts": partition_counts,
        "selected_100_records": selected_100_records,
        "leakage_detected": len(leakage) > 0,
        "leakage_count": len(leakage),
        "leakage_sample": leakage[:20],
    }


def load_benchmark_partitions(path: Path | str | None = None) -> list[dict[str, Any]]:
    """Load the saved benchmark records."""
    if path is None:
        path = _default_output_path()
    else:
        path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("records", [])


def load_benchmark_metadata(path: Path | str | None = None) -> dict[str, Any]:
    """Load the saved benchmark metadata."""
    if path is None:
        path = _default_output_path()
    else:
        path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    return {}


if __name__ == "__main__":
    build_benchmark_partitions()
