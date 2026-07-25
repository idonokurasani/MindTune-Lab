#!/usr/bin/env python3
"""Generate the versioned canonical 320-verb Hebrew curriculum.

Usage:
    PYTHONPATH=/path/to/repo .venv/bin/python scripts/generate_curriculum_320.py
"""
from __future__ import annotations

from datetime import datetime, timezone

from hebrew.morphology import morphology_features_to_form_key, parse_morphology_tag
from hebrew.phase3.data_loader import Phase3DataLoader
from hebrew.phase3.selection import select_100_verbs
from mantra.phase1.curriculum import (
    CURRICULUM_PATH,
    Curriculum,
    CurriculumVerb,
    hebrew_infinitive_to_latin_slug,
)


def _vocalized_infinitive(
    group_rows: list[dict[str, str]], pattern: str, table_number: int
) -> str | None:
    for row in group_rows:
        features = parse_morphology_tag(row["morphology"], pattern, table_number)
        form_key = morphology_features_to_form_key(features)
        if form_key == "infinitive":
            return row["vocalized_inflection"]
    return None


def main() -> None:
    loader = Phase3DataLoader()
    loader.load_all()

    # Select enough verbs so that, after filtering for an infinitive form,
    # we retain a full 320.
    candidates = select_100_verbs(loader, target_size=400)
    with_infinitive = [c for c in candidates if c["infinitive_plain"]]
    selected = with_infinitive[:320]

    groups = loader.verb_groups()
    verbs: list[CurriculumVerb] = []

    for idx, candidate in enumerate(selected, start=1):
        pattern = candidate["pattern"]
        table_number = candidate["table_number"]
        base_form = candidate["base_form_plain"]
        group_rows = groups.get((pattern, table_number, base_form), [])
        inf_vocalized = _vocalized_infinitive(group_rows, pattern, table_number)
        inf_plain = candidate["infinitive_plain"]

        if inf_vocalized is None:
            inf_vocalized = inf_plain

        asset_prefix = hebrew_infinitive_to_latin_slug(inf_vocalized)
        # Ensure uniqueness by appending a counter if necessary.
        existing_prefixes = {v.asset_id_prefix for v in verbs}
        unique_prefix = asset_prefix
        counter = 2
        while unique_prefix in existing_prefixes:
            unique_prefix = f"{asset_prefix}_{counter}"
            counter += 1

        verb = CurriculumVerb(
            verb_id=inf_plain,
            asset_id_prefix=unique_prefix,
            infinitive_pointed=inf_vocalized,
            infinitive_plain=inf_plain,
            italian_infinitive="",
            root=candidate["root"],
            binyan=candidate["binyan"],
            pattern=pattern,
            table_number=table_number,
            frequency=int(candidate["frequency"]),
            priority=idx,
            selection_reason=list(candidate.get("selection_reason", [])),
        )
        verbs.append(verb)

    curriculum = Curriculum(
        version="1.0.0",
        generated_at=datetime.now(timezone.utc).isoformat(),
        source="hebrew.phase3.eran_tomer",
        verbs=verbs,
    )

    curriculum.save(CURRICULUM_PATH)
    print(f"Wrote {len(curriculum.verbs)} verbs to {CURRICULUM_PATH}")


if __name__ == "__main__":
    main()
