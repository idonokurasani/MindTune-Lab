"""Build the 100-verb verified-consensus expansion set.

Each record carries independent evidence groups and a status from the
confidence engine.  Records are not called "gold" unless they come from the
frozen external benchmark; internal candidates are high_confidence_candidate,
verified_consensus, disputed, unresolved, or rejected.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from ..morphology import morphology_features_to_form_key, parse_morphology_tag
from ..normalization import normalize_hebrew, standard_unvocalized, strip_niqqud
from .confidence import confidence_from_evidence
from .data_loader import Phase3DataLoader
from .selection import select_100_verbs


def _load_orthography() -> Any:
    try:
        from .. import orthography
        return orthography
    except Exception:
        return None


def _load_phonology() -> Any:
    try:
        from .. import phonology
        return phonology
    except Exception:
        return None


def _verb_inflector_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "hebrew_resources"
        / "vendor"
        / "Hebrew-Resources"
        / "code"
        / "VerbInflector"
        / "resources"
        / "Inflected verbs Extended.txt"
    )


def _load_verb_inflector_forms() -> dict[tuple[str, int, str, str], set[str]]:
    """Build a map of generated surfaces from the fresh Verb Inflector output.

    This is a separate generation pass from the Eran Tomer CSV, even though the
    underlying code base is the same.  It serves as an independent production
    evidence group.
    """
    generated: dict[tuple[str, int, str, str], set[str]] = {}
    path = _verb_inflector_path()
    if not path.exists():
        return generated
    with path.open("r", encoding="utf-8", newline="") as f:
        for cells in csv.reader(f):
            if len(cells) != 5:
                continue
            pattern, table_str, surface, morph, base_form = cells
            try:
                table_number = int(table_str)
            except ValueError:
                continue
            features = parse_morphology_tag(morph, pattern, table_number)
            form_key = morphology_features_to_form_key(features)
            base_plain = strip_niqqud(base_form)
            key = (pattern, table_number, base_plain, form_key)
            generated.setdefault(key, set()).add(normalize_hebrew(surface))
    return generated


def _canonical_unvocalized(vocalized: str, root: str, binyan: str, form_key: str) -> dict[str, Any]:
    orth = _load_orthography()
    if orth is not None and hasattr(orth, "canonical_unvocalized"):
        try:
            return orth.canonical_unvocalized(vocalized, root, binyan, form_key)
        except Exception:
            pass
    spelling = standard_unvocalized(vocalized)
    return {
        "spelling": spelling,
        "class": "fallback",
        "rule_trace": ["standard_unvocalized_fallback"],
        "confidence": 0.5,
        "unresolved": False,
        "variants": {"full": spelling, "defective": spelling, "common_nonstandard": [], "rejected": []},
    }


def _pronunciation(vocalized: str, root: str, binyan: str, form_key: str) -> dict[str, Any]:
    phon = _load_phonology()
    if phon is not None and hasattr(phon, "PronunciationValidator"):
        try:
            validator = phon.PronunciationValidator()
            return validator.validate(vocalized, root=root, binyan=binyan, form_key=form_key)
        except Exception:
            pass
    return {
        "phonemic": "",
        "practical": "",
        "syllabification": [],
        "lexical_stress": 0,
        "shva_status": "not_applicable",
        "dagesh_status": [],
        "begadkefat": {},
        "variants": [],
        "rule_trace": ["pronunciation_unavailable"],
        "phonikud_proposal": "",
        "override_comparison": False,
        "confidence": 0.0,
        "unresolved": True,
    }


def build_automatic_gold_100(
    loader: Phase3DataLoader | None = None,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Generate the 100-verb expansion fixture and a status report."""
    if loader is None:
        loader = Phase3DataLoader()
        loader.load_all()
    if output_path is None:
        output_path = Path(__file__).resolve().parents[2] / "data" / "hebrew" / "phase3" / "automatic_gold_100.json"
    else:
        output_path = Path(output_path)

    selected = select_100_verbs(loader)
    groups = loader.verb_groups()
    corpus = loader.corpus_counts()
    inflector_forms = _load_verb_inflector_forms()

    records: list[dict[str, Any]] = []
    status_counter: dict[str, int] = {}

    for verb in selected:
        key = (verb["pattern"], verb["table_number"], verb["base_form_plain"])
        rows = groups.get(key, [])
        if not rows:
            continue

        infinitive_vocalized = ""
        for row in rows:
            if row["morphology"].startswith("INFINITIVE"):
                infinitive_vocalized = row["vocalized_inflection"]
                break
        if not infinitive_vocalized:
            infinitive_vocalized = rows[0]["vocalized_inflection"]

        forms: list[dict[str, Any]] = []
        seen_form_ids: set[str] = set()
        for row in rows:
            vocalized = row["vocalized_inflection"]
            plain = strip_niqqud(vocalized)
            morph = row["morphology"]
            features = parse_morphology_tag(morph, verb["pattern"], verb["table_number"])
            form_key = morphology_features_to_form_key(features)
            form_id = f"{verb['group_key']}::{form_key}"
            if form_id in seen_form_ids:
                continue
            seen_form_ids.add(form_id)
            count = corpus.get((normalize_hebrew(plain), form_key), 0)

            orth = _canonical_unvocalized(vocalized, verb["root"], verb["binyan"], form_key)
            pron = _pronunciation(vocalized, verb["root"], verb["binyan"], form_key)

            inflector_key = (verb["pattern"], verb["table_number"], verb["base_form_plain"], form_key)
            inflector_surfaces = inflector_forms.get(inflector_key, set())
            norm_vocalized = normalize_hebrew(vocalized)
            inflector_agrees = norm_vocalized in inflector_surfaces

            verb_inflector_evidence: dict[str, Any] = {
                "present": bool(inflector_surfaces),
                "generated_surfaces": sorted(inflector_surfaces)[:10] if inflector_surfaces else [],
                "group": "verb_inflector_fresh_pass",
            }
            if inflector_agrees:
                verb_inflector_evidence["surface_vocalized"] = norm_vocalized
                verb_inflector_evidence["agrees"] = True

            evidence = {
                "canonical": {"surface_vocalized": vocalized},
                "eran_tomer": {"present": True, "surface_vocalized": vocalized, "agrees": True, "group": "eran_tomer_derivative"},
                "verb_inflector": verb_inflector_evidence,
                "corpus": {"present": count > 0, "count": count, "group": "corpus_attestation"},
            }

            # Phonology disagreements are recorded on the pronunciation object but
            # do not by themselves block a spelling/morphology consensus.
            orth_unresolved = orth.get("unresolved", False) and "standard_unvocalized_fallback" not in orth.get("rule_trace", [])
            confidence, status = confidence_from_evidence(
                evidence,
                corpus_count=count,
                rule_trace=orth.get("rule_trace", []),
                unresolved=orth_unresolved,
            )

            # Corpus-only evidence without production corroboration stays unresolved.
            if status == "high_confidence_candidate" and count < 2:
                status = "unresolved"
                confidence = 0.0

            status_counter[status] = status_counter.get(status, 0) + 1

            forms.append(
                {
                    "form_id": f"{verb['group_key']}::{form_key}",
                    "form_key": form_key,
                    "morphology_tag": morph,
                    "surface_vocalized": vocalized,
                    "surface_plain": plain,
                    "canonical_unvocalized": orth.get("spelling", plain),
                    "canonical_class": orth.get("class", "unknown"),
                    "canonical_variants": orth.get("variants", {}),
                    "pronunciation": pron,
                    "root": verb["root"],
                    "binyan": verb["binyan"],
                    "pattern": verb["pattern"],
                    "table_number": verb["table_number"],
                    "corpus_count": count,
                    "status": status,
                    "confidence": confidence,
                    "evidence": evidence,
                    "disagreements": [],
                    "rule_trace": orth.get("rule_trace", []),
                    "orthography_unresolved": orth.get("unresolved", False),
                    "phonology_unresolved": pron.get("unresolved", True),
                }
            )

        records.append(
            {
                "verb_id": verb["group_key"],
                "infinitive_vocalized": infinitive_vocalized,
                "infinitive_plain": verb["infinitive_plain"],
                "representative_plain": verb["representative_plain"],
                "root": verb["root"],
                "binyan": verb["binyan"],
                "pattern": verb["pattern"],
                "table_number": verb["table_number"],
                "selection_reason": verb["selection_reason"],
                "root_class": verb["root_class"],
                "frequency": verb["frequency"],
                "forms": forms,
            }
        )

    result = {
        "source": "automatic_100_verb_expansion",
        "description": "High-frequency Modern Israeli Hebrew verbs selected for Phase 3 expansion.",
        "generated_from": ["eran_tomer", "verb_inflector", "corpus_counts"],
        "record_count": len(records),
        "status_summary": status_counter,
        "verbs": records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    build_automatic_gold_100()
