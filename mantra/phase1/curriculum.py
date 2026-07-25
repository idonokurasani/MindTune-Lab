"""Versioned Hebrew curriculum and Mantra selection policy.

This module lives in the protocol layer, not the audio runtime.  It knows
nothing about EEG and never calls TTS.  It selects a verb from the canonical
curriculum based on explicit learner-state signals, then hands an asset
sequence to the audio runtime for execution.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .asset_contract import AudioAssetRequirement, build_compact_mantra_requirements
from .utils import normalize_unicode

CURRICULUM_PATH = Path("data/hebrew/curriculum_v1_320.json")

# Niqqud code points used by the slug transliterator.  Kept local so this
# module does not depend on phonikud-heavy hebrew.phonology.
_NIQQUD_NAME: dict[str, str] = {
    "\u05b0": "sheva",
    "\u05b1": "hataf_segol",
    "\u05b2": "hataf_patah",
    "\u05b3": "hataf_qamats",
    "\u05b4": "hiriq",
    "\u05b5": "tsere",
    "\u05b6": "segol",
    "\u05b7": "patah",
    "\u05b8": "qamats",
    "\u05b9": "holam",
    "\u05bb": "qubuts",
    "\u05bc": "dagesh",
    "\u05c7": "qamats_qatan",
}

_VOWEL_POINTS = frozenset(c for c in _NIQQUD_NAME if _NIQQUD_NAME[c] != "dagesh")

_VOWEL_CHAR: dict[str, str] = {
    "sheva": "e",
    "hataf_segol": "e",
    "hataf_patah": "a",
    "hataf_qamats": "o",
    "hiriq": "i",
    "tsere": "e",
    "segol": "e",
    "patah": "a",
    "qamats": "a",
    "holam": "o",
    "qubuts": "u",
    "qamats_qatan": "o",
}

# Map final Hebrew forms to non-final for consonant lookup.
_FINAL_MAP: dict[str, str] = {
    "\u05da": "\u05db",  # final kaf
    "\u05dd": "\u05de",  # final mem
    "\u05df": "\u05e0",  # final nun
    "\u05e3": "\u05e4",  # final pe
    "\u05e5": "\u05e6",  # final tsadi
}


@dataclass(frozen=True)
class CurriculumVerb:
    """One canonical verb in the curriculum."""

    verb_id: str
    asset_id_prefix: str
    infinitive_pointed: str
    infinitive_plain: str
    italian_infinitive: str | None = None
    root: str = ""
    binyan: str = ""
    pattern: str = ""
    table_number: int = 0
    frequency: int = 0
    priority: int = 0
    selection_reason: list[str] = field(default_factory=list)
    source_group_key: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CurriculumVerb":
        data = dict(data)
        if data.get("italian_infinitive") == "":
            data["italian_infinitive"] = None
        data["infinitive_pointed"] = unicodedata.normalize(
            "NFC", data.get("infinitive_pointed", "")
        )
        data["infinitive_plain"] = unicodedata.normalize(
            "NFC", data.get("infinitive_plain", "")
        )
        return cls(**data)

    def required_asset_ids(self) -> list[str]:
        """Asset IDs required for a complete compact mantra."""
        p = self.asset_id_prefix
        assets = [f"he.{p}.infinitive"]
        if self.italian_infinitive:
            assets.append(f"it.{p}.infinitive")
        for key in ["ms", "fs", "mp", "fp"]:
            assets.append(f"he.{p}.present.{key}")
        for key in [
            "1sg",
            "2msg",
            "2fsg",
            "3msg",
            "3fsg",
            "1pl",
            "2mpl",
            "2fpl",
            "3pl",
        ]:
            assets.append(f"he.{p}.past.{key}")
        for key in ["1sg", "2msg", "2fsg", "3msg", "3fsg", "1pl", "2pl", "3pl"]:
            assets.append(f"he.{p}.future.{key}")
        for key in ["ms", "fs", "pl"]:
            assets.append(f"he.{p}.imperative.{key}")
        return assets


@dataclass
class Curriculum:
    """Versioned canonical curriculum."""

    version: str
    generated_at: str | None
    source: str
    verbs: list[CurriculumVerb]

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "version": self.version,
            "source": self.source,
            "verbs": [v.to_dict() for v in self.verbs],
        }
        if self.generated_at is not None:
            result["generated_at"] = self.generated_at
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Curriculum":
        return cls(
            version=data["version"],
            generated_at=data.get("generated_at"),
            source=data["source"],
            verbs=[CurriculumVerb.from_dict(v) for v in data["verbs"]],
        )

    def save(self, path: Path = CURRICULUM_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = CURRICULUM_PATH) -> "Curriculum":
        if not path.exists():
            raise FileNotFoundError(f"Curriculum not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def by_verb_id(self) -> dict[str, CurriculumVerb]:
        return {v.verb_id: v for v in self.verbs}


@dataclass(frozen=True)
class LearnerState:
    """Explicit signals used by the selection policy.

    All fields are optional; missing signals are treated as empty.
    """

    scheduled_new_content: tuple[str, ...] = ()
    overdue_review: tuple[str, ...] = ()
    recent_domino_errors: dict[str, int] = field(default_factory=dict)
    recall_scores: dict[str, float] = field(default_factory=dict)
    last_exposure_hours: dict[str, float] = field(default_factory=dict)
    curriculum_priority: dict[str, int] = field(default_factory=dict)
    recent_exposure_limit_hours: float = 24.0
    low_recall_threshold: float = 0.6


@dataclass(frozen=True)
class MantraSelectionResult:
    """Result of a policy decision."""

    verb_id: str
    asset_id_prefix: str
    reason_code: str
    policy_version: str
    eligible_verbs: tuple[str, ...]
    selected_verb: CurriculumVerb | None = None
    missing_assets: tuple[str, ...] = ()


def _is_hebrew_letter(char: str) -> bool:
    return "\u0590" <= char <= "\u05ff" and not _is_niqqud(char)


def _is_niqqud(char: str) -> bool:
    return ("\u0591" <= char <= "\u05bd" or char in "\u05bf\u05c0\u05c1\u05c2\u05c3\u05c4\u05c5\u05c6\u05c7")


def _letter_clusters(vocalized: str) -> list[dict[str, Any]]:
    """Split vocalized text into base-letter clusters with diacritics."""
    text = normalize_unicode(vocalized)
    chars = list(unicodedata.normalize("NFD", text))
    clusters: list[dict[str, Any]] = []
    i = 0
    n = len(chars)
    while i < n:
        c = chars[i]
        if not _is_hebrew_letter(c):
            i += 1
            continue
        marks: list[str] = []
        j = i + 1
        while j < n and _is_niqqud(chars[j]):
            marks.append(chars[j])
            j += 1
        clusters.append({"base": c, "marks": marks})
        i = j
    return clusters


def _vowel_name(marks: list[str]) -> str | None:
    for m in marks:
        if m in _VOWEL_POINTS:
            return _NIQQUD_NAME[m]
    return None


def _has_dagesh(marks: list[str]) -> bool:
    return any(m == "\u05bc" for m in marks)


def _has_shin(marks: list[str]) -> bool:
    return any(m == "\u05c1" for m in marks)


def _has_sin(marks: list[str]) -> bool:
    return any(m == "\u05c2" for m in marks)


def _consonant_for_cluster(cluster: dict[str, Any]) -> str:
    base = _FINAL_MAP.get(cluster["base"], cluster["base"])
    marks = cluster["marks"]
    dagesh = _has_dagesh(marks)
    if _has_shin(marks):
        return "sh"
    if _has_sin(marks):
        return "s"
    if base == "\u05d1":  # bet
        return "b" if dagesh else "v"
    if base in ("\u05db", "\u05da"):  # kaf
        return "k" if dagesh else "ch"
    if base in ("\u05e4", "\u05e3"):  # pe
        return "p" if dagesh else "f"
    mapping = {
        "\u05d0": "",
        "\u05d2": "g",
        "\u05d3": "d",
        "\u05d4": "h",
        "\u05d5": "v",
        "\u05d6": "z",
        "\u05d7": "ch",
        "\u05d8": "t",
        "\u05d9": "y",
        "\u05dc": "l",
        "\u05de": "m",
        "\u05dd": "m",
        "\u05e0": "n",
        "\u05df": "n",
        "\u05e1": "s",
        "\u05e2": "",
        "\u05e6": "tz",
        "\u05e5": "tz",
        "\u05e7": "k",
        "\u05e8": "r",
        "\u05e9": "s",
        "\u05ea": "t",
    }
    return mapping.get(base, "")


def hebrew_infinitive_to_latin_slug(vocalized: str) -> str:  # noqa: C901
    """Return a stable ASCII slug for a vocalized Hebrew infinitive.

    This is a conservative, rule-based transliteration tuned for infinitives.
    It is not a full phonemic engine and should not be used for pronunciation.
    """
    clusters = _letter_clusters(vocalized)
    segments: list[str] = []

    def _append_to_previous(vowel: str) -> None:
        if segments:
            segments[-1] += vowel
        else:
            segments.append(vowel)

    for i, cluster in enumerate(clusters):
        base = _FINAL_MAP.get(cluster["base"], cluster["base"])
        marks = cluster["marks"]
        vowel_name = _vowel_name(marks)
        has_dagesh = _has_dagesh(marks)

        # vav / yud as vowel carriers
        if base == "\u05d5":  # vav
            if vowel_name in ("holam", "qamats_qatan"):
                _append_to_previous("o")
                continue
            if vowel_name == "qubuts" or has_dagesh:
                _append_to_previous("u")
                continue
            # consonantal vav
            segments.append("v")
            continue

        vowel_char = ""
        if vowel_name == "sheva":
            # First lamed in an infinitive prefix: "le"/"la"/"li"/"lo"/"lu".
            if i == 0 and base == "\u05dc":
                vowel_char = "e"
            else:
                # Silent sheva if the vowel appears within the next two clusters.
                future = clusters[i + 1 : i + 3]
                if any(_vowel_name(c.get("marks", [])) not in (None, "sheva") for c in future):
                    vowel_char = ""
                else:
                    vowel_char = "e"
        elif vowel_name is not None:
            vowel_char = _VOWEL_CHAR.get(vowel_name, "")

        if base == "\u05d9":  # yod
            if vowel_name and vowel_name != "sheva":
                # yod is a vowel carrier (mater): attach to previous consonant.
                _append_to_previous(vowel_char)
                continue
            # yod with no vowel: consonantal, silent mater, or part of "yo/yu".
            if segments and segments[-1] and segments[-1][-1] in "aeiou":
                future = clusters[i + 1 : i + 2]
                if not (
                    future
                    and future[0]["base"] == "\u05d5"
                    and (
                        _vowel_name(future[0].get("marks", [])) in ("holam", "qubuts", "qamats_qatan")
                        or _has_dagesh(future[0].get("marks", []))
                    )
                ):
                    continue
            segments.append("y")
            continue

        if base in ("\u05d0", "\u05e2"):  # alef / ayin
            if vowel_char:
                _append_to_previous(vowel_char)
            continue

        consonant = _consonant_for_cluster(cluster)
        if not consonant and not vowel_char:
            continue
        segments.append(consonant + vowel_char)

    raw = "".join(segments).lower()
    # Keep only letters.
    return re.sub(r"[^a-z]", "", raw)


class MantraSelectionPolicy:
    """Deterministic policy that selects the next verb for a mantra.

    The policy never calls TTS and never reads EEG.  It selects from the
    eligible curriculum based on explicit learner-state signals, and it
    filters to verbs whose audio assets are available unless the caller
    explicitly requests asset-preparation mode.
    """

    POLICY_VERSION = "1.0.0"

    def __init__(
        self,
        curriculum: Curriculum,
        available_assets: set[str] | None = None,
        readiness_source: Any | None = None,
    ):
        self.curriculum = curriculum
        self._verb_map = curriculum.by_verb_id()
        self.available_assets = available_assets or set()
        self.readiness_source = readiness_source

    def _assets_ready(
        self,
        verb: CurriculumVerb,
        *,
        asset_preparation_mode: bool = False,
    ) -> bool:
        if self.readiness_source is not None:
            report = self.readiness_source.evaluate(
                verb, asset_preparation_mode=asset_preparation_mode
            )
            if asset_preparation_mode:
                return bool(report.asset_preparation_eligibility.value == "eligible")
            return bool(report.learner_execution_eligibility.value == "eligible")
        required = set(verb.required_asset_ids())
        return required.issubset(self.available_assets)

    def _missing_assets(
        self,
        verb: CurriculumVerb,
        *,
        asset_preparation_mode: bool = False,
    ) -> set[str]:
        if self.readiness_source is not None:
            report = self.readiness_source.evaluate(
                verb, asset_preparation_mode=asset_preparation_mode
            )
            if report.asset_report is not None:
                return {str(x) for x in report.asset_report.missing}
            return set()
        return set(verb.required_asset_ids()) - self.available_assets

    def _eligible_verbs(
        self,
        state: LearnerState,
        *,
        asset_preparation_mode: bool = False,
    ) -> list[CurriculumVerb]:
        """Return verbs that are candidates for selection."""
        eligible: list[CurriculumVerb] = []
        for verb in self.curriculum.verbs:
            if not asset_preparation_mode and not self._assets_ready(verb, asset_preparation_mode=asset_preparation_mode):
                continue
            # Respect recent exposure limits.
            hours_since = state.last_exposure_hours.get(verb.verb_id, float("inf"))
            if hours_since < state.recent_exposure_limit_hours:
                continue
            eligible.append(verb)
        return eligible

    def _priority(self, verb: CurriculumVerb, state: LearnerState) -> int:
        return state.curriculum_priority.get(verb.verb_id, verb.priority)

    def select(  # noqa: C901
        self,
        state: LearnerState,
        *,
        asset_preparation_mode: bool = False,
    ) -> MantraSelectionResult:
        """Select a verb and return a typed result with reason code."""
        eligible = self._eligible_verbs(state, asset_preparation_mode=asset_preparation_mode)
        eligible_ids = tuple(v.verb_id for v in eligible)

        if not eligible:
            if asset_preparation_mode:
                # In preparation mode, pick the highest-priority verb that is
                # missing assets, regardless of exposure limits.
                candidates = list(self.curriculum.verbs)
                candidates.sort(key=lambda v: (-self._priority(v, state), -v.frequency))
                for verb in candidates:
                    missing = self._missing_assets(verb, asset_preparation_mode=True)
                    if missing:
                        return MantraSelectionResult(
                            verb_id=verb.verb_id,
                            asset_id_prefix=verb.asset_id_prefix,
                            reason_code="asset_preparation",
                            policy_version=self.POLICY_VERSION,
                            eligible_verbs=eligible_ids,
                            selected_verb=verb,
                            missing_assets=tuple(sorted(missing)),
                        )
            return MantraSelectionResult(
                verb_id="",
                asset_id_prefix="",
                reason_code="no_eligible_verb",
                policy_version=self.POLICY_VERSION,
                eligible_verbs=eligible_ids,
            )

        # 1. Scheduled new content.
        for verb_id in state.scheduled_new_content:
            if verb_id in self._verb_map:
                verb = self._verb_map[verb_id]
                if verb in eligible:
                    return self._result(verb, "scheduled_new_content", eligible_ids)

        # 2. Overdue review.
        if state.overdue_review:
            overdue = [self._verb_map[vid] for vid in state.overdue_review if vid in self._verb_map and self._verb_map[vid] in eligible]
            overdue.sort(
                key=lambda v: (
                    state.recall_scores.get(v.verb_id, 1.0),
                    -v.frequency,
                )
            )
            if overdue:
                return self._result(overdue[0], "overdue_review", eligible_ids)

        # 3. Recent Domino errors.
        if state.recent_domino_errors:
            error_verbs = [
                self._verb_map[vid]
                for vid, _ in sorted(
                    state.recent_domino_errors.items(), key=lambda kv: -kv[1]
                )
                if vid in self._verb_map and self._verb_map[vid] in eligible
            ]
            if error_verbs:
                # Prefer the error verb with the lowest recall score.
                error_verbs.sort(
                    key=lambda v: (
                        state.recall_scores.get(v.verb_id, 1.0),
                        -state.recent_domino_errors.get(v.verb_id, 0),
                        -v.frequency,
                    )
                )
                return self._result(error_verbs[0], "domino_error", eligible_ids)

        # 4. Low recall performance.
        low_recall = [
            v
            for v in eligible
            if state.recall_scores.get(v.verb_id, 1.0) < state.low_recall_threshold
        ]
        if low_recall:
            low_recall.sort(
                key=lambda v: (
                    state.recall_scores.get(v.verb_id, 1.0),
                    -self._priority(v, state),
                    -v.frequency,
                )
            )
            return self._result(low_recall[0], "low_recall", eligible_ids)

        # 5. Default: next new curriculum verb by priority/frequency.
        eligible.sort(key=lambda v: (-self._priority(v, state), -v.frequency))
        if eligible:
            if asset_preparation_mode:
                # In preparation mode, prefer verbs that are missing assets.
                for verb in eligible:
                    if not self._assets_ready(verb, asset_preparation_mode=True):
                        return self._result(verb, "asset_preparation", eligible_ids)
                return self._result(eligible[0], "curriculum_priority", eligible_ids)
            return self._result(eligible[0], "curriculum_priority", eligible_ids)

        return MantraSelectionResult(
            verb_id="",
            asset_id_prefix="",
            reason_code="no_eligible_verb",
            policy_version=self.POLICY_VERSION,
            eligible_verbs=eligible_ids,
        )

    def _result(
        self,
        verb: CurriculumVerb,
        reason_code: str,
        eligible_verbs: tuple[str, ...],
    ) -> MantraSelectionResult:
        missing = self._missing_assets(verb)
        return MantraSelectionResult(
            verb_id=verb.verb_id,
            asset_id_prefix=verb.asset_id_prefix,
            reason_code=reason_code,
            policy_version=self.POLICY_VERSION,
            eligible_verbs=eligible_verbs,
            selected_verb=verb,
            missing_assets=tuple(sorted(missing)),
        )


def plan_compact_mantra(
    verb: CurriculumVerb,
    *,
    include_italian_intro: bool = True,
) -> list[str]:
    """Return the asset-id sequence for a compact mantra execution plan."""
    p = verb.asset_id_prefix
    sequence: list[str] = []
    if include_italian_intro and verb.italian_infinitive:
        sequence.append(f"it.{p}.infinitive")
    sequence.append(f"he.{p}.infinitive")
    for key in ["ms", "fs", "mp", "fp"]:
        sequence.append(f"he.{p}.present.{key}")
    for key in [
        "1sg",
        "2msg",
        "2fsg",
        "3msg",
        "3fsg",
        "1pl",
        "2mpl",
        "2fpl",
        "3pl",
    ]:
        sequence.append(f"he.{p}.past.{key}")
    for key in ["1sg", "2msg", "2fsg", "3msg", "3fsg", "1pl", "2pl", "3pl"]:
        sequence.append(f"he.{p}.future.{key}")
    for key in ["ms", "fs", "pl"]:
        sequence.append(f"he.{p}.imperative.{key}")
    return sequence


@dataclass
class MantraExecutionPlan:
    """Execution plan handed from protocol layer to audio runtime."""

    verb_id: str
    asset_id_prefix: str
    asset_sequence: list[str]
    reason_code: str
    policy_version: str
    output_path: Path | None = None
    requirements: list[AudioAssetRequirement] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verb_id": self.verb_id,
            "asset_id_prefix": self.asset_id_prefix,
            "asset_sequence": self.asset_sequence,
            "reason_code": self.reason_code,
            "policy_version": self.policy_version,
            "output_path": str(self.output_path) if self.output_path else None,
            "requirements": [r.to_dict() for r in self.requirements] if self.requirements else None,
        }


def build_execution_plan(
    curriculum: Curriculum,
    state: LearnerState,
    output_dir: Path,
    available_assets: set[str] | None = None,
    readiness_source: Any | None = None,
    audio_profile: Any | None = None,
    *,
    asset_preparation_mode: bool = False,
) -> MantraExecutionPlan:
    """Protocol-layer helper: select a verb and build an audio execution plan."""
    policy = MantraSelectionPolicy(
        curriculum,
        available_assets=available_assets,
        readiness_source=readiness_source,
    )
    result = policy.select(state, asset_preparation_mode=asset_preparation_mode)
    if result.selected_verb is None:
        return MantraExecutionPlan(
            verb_id="",
            asset_id_prefix="",
            asset_sequence=[],
            reason_code=result.reason_code,
            policy_version=result.policy_version,
        )
    requirements: list[AudioAssetRequirement] | None = None
    if readiness_source is not None and audio_profile is not None:
        report = readiness_source.evaluate(result.selected_verb)
        if report.specification is not None:
            requirements = build_compact_mantra_requirements(
                report.specification, audio_profile
            )
            sequence = [r.asset_id for r in requirements]
        else:
            sequence = plan_compact_mantra(result.selected_verb)
    else:
        sequence = plan_compact_mantra(result.selected_verb)
    safe_prefix = re.sub(r"[^a-z0-9_\-]", "_", result.selected_verb.asset_id_prefix)
    output_path = output_dir / f"mantra_{safe_prefix}.wav"
    return MantraExecutionPlan(
        verb_id=result.verb_id,
        asset_id_prefix=result.selected_verb.asset_id_prefix,
        asset_sequence=sequence,
        reason_code=result.reason_code,
        policy_version=result.policy_version,
        output_path=output_path,
        requirements=requirements,
    )
