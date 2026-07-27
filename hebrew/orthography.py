"""Normative Modern Israeli Hebrew orthography for verb forms.

This module centralises deterministic rules for converting pointed Hebrew verb
forms into a canonical unvocalised spelling, with rule traces and a full set of
spelling classes (full / defective / common nonstandard / rejected).

It is intentionally decoupled from any LLM evaluator and can be unit-tested
purely against the vocalised input, the root, the binyan and the form key.
"""

from __future__ import annotations

from .normalization import (
    decompose,
    is_hebrew_letter,
    is_niqqud,
    normalize_unicode,
    standard_unvocalized,
    strip_niqqud,
)

GUTTURAL = frozenset("אהחע")
VOWEL_MATERS = frozenset("וי")
IRREGULAR_ROOTS = frozenset([("ה", "י", "ה")])

HOLAM = "\u05b9"
QUBUTS = "\u05bb"


def _parse_root(root: str) -> list[str]:
    """Return just the Hebrew letters of a root string (e.g. 'כ-ת-ב' or 'כתב')."""
    return [c for c in normalize_unicode(root) if is_hebrew_letter(c)]


def _form_context(form_key: str) -> dict:
    """Infer morphological context from a form key such as 'past_second_f_singular'
    or 'PAST+SECOND+F+SINGULAR+MISSING'.
    """
    ctx = {
        "infinitive": False,
        "imperative": False,
        "future": False,
        "past": False,
        "present": False,
        "beinoni": False,
        "participle": False,
        "person": "",
        "gender": "",
        "number": "",
    }
    if not form_key:
        return ctx
    norm = form_key.lower().replace("+", " ").replace("_", " ").replace("-", " ")
    tokens = set(norm.split())
    ctx["infinitive"] = "infinitive" in tokens or "inf" in tokens
    ctx["imperative"] = "imperative" in tokens or "imp" in tokens
    ctx["future"] = "future" in tokens or "fut" in tokens
    ctx["past"] = "past" in tokens
    ctx["present"] = "present" in tokens
    ctx["beinoni"] = "beinoni" in tokens
    ctx["participle"] = "participle" in tokens or ctx["beinoni"]
    if "first" in tokens:
        ctx["person"] = "first"
    elif "second" in tokens:
        ctx["person"] = "second"
    elif "third" in tokens:
        ctx["person"] = "third"
    if "masculine" in tokens or "m" in tokens:
        ctx["gender"] = "masculine"
    elif "feminine" in tokens or "f" in tokens:
        ctx["gender"] = "feminine"
    if "singular" in tokens or "sg" in tokens:
        ctx["number"] = "singular"
    elif "plural" in tokens or "pl" in tokens:
        ctx["number"] = "plural"
    return ctx


def _letter_clusters(text: str) -> list[tuple[str, list[str], bool]]:
    """Decompose *text* into (base_letter, diacritics, is_last_letter) clusters."""
    chars = list(decompose(text))
    n = len(chars)
    clusters: list[tuple[str, list[str], bool]] = []
    i = 0
    while i < n:
        c = chars[i]
        if not is_hebrew_letter(c):
            clusters.append((c, [], True))
            i += 1
            continue
        marks: list[str] = []
        j = i + 1
        while j < n and is_niqqud(chars[j]):
            marks.append(chars[j])
            j += 1
        is_last = True
        k = j
        while k < n:
            if is_hebrew_letter(chars[k]):
                is_last = False
                break
            k += 1
        clusters.append((c, marks, is_last))
        i = j
    return clusters


def _is_first_root_letter(letter: str, root: str) -> bool:
    letters = _parse_root(root)
    return bool(letters) and letter == letters[0]


def _is_in_root(letter: str, root: str) -> bool:
    return letter in _parse_root(root)


def _qubuts_decision(letter: str, idx: int, clusters: list, trace: list) -> str:
    """Qubuts (/u/) is normally represented by a ו mater in full spelling."""
    if idx + 1 < len(clusters) and clusters[idx + 1][0] in VOWEL_MATERS:
        trace.append(f"qubuts_explicit_mater_after_{letter}")
        return "no_insert"
    trace.append(f"qubuts_after_{letter}_requires_vav")
    return "insert"


def _holam_decision(
    letter: str,
    idx: int,
    clusters: list,
    root: str,
    root_class: dict,
    form_ctx: dict,
    trace: list,
) -> str:
    """Return one of: 'insert', 'forbidden', 'optional', 'no_insert'."""
    if idx + 1 < len(clusters) and clusters[idx + 1][0] in VOWEL_MATERS:
        trace.append(f"holam_explicit_mater_after_{letter}")
        return "no_insert"

    # Infinitives, imperatives and futures with holam have a long /o/ that is
    # normally written plene (with vav).
    for ctx_name in ("infinitive", "imperative", "future"):
        if form_ctx.get(ctx_name):
            trace.append(f"holam_{ctx_name}_after_{letter}_requires_vav")
            return "insert"

    if form_ctx.get("past"):
        # Hollow roots retain the vav mater when the middle radical drops:
        # ב-ו-שׁ -> בֹּשְׁתְּ -> בושת.
        if root_class.get("hollow") and _is_first_root_letter(letter, root):
            trace.append(f"holam_hollow_first_radical_after_{letter}_requires_vav")
            return "insert"
        # A holam on a guttural in the past is normally a qamats-qatan /a/
        # mis-encoded as holam; a vav would wrongly imply /o/.
        if _is_in_root(letter, root) and letter in GUTTURAL:
            trace.append(f"holam_guttural_past_after_{letter}_forbidden")
            return "forbidden"
        # Other past holam cases (e.g. יָכֹלְתָּ, קָטֹנְתְּ) are genuinely
        # ambiguous between full and defective spellings.
        trace.append(f"holam_past_after_{letter}_optional_unresolved")
        return "optional"

    if form_ctx.get("present") or form_ctx.get("beinoni") or form_ctx.get("participle"):
        if _is_in_root(letter, root) and letter in GUTTURAL:
            trace.append(f"holam_guttural_present_after_{letter}_optional_unresolved")
            return "optional"
        trace.append(f"holam_present_after_{letter}_requires_vav")
        return "insert"

    trace.append(f"holam_default_after_{letter}_requires_vav")
    return "insert"


def classify_root_orthographic_class(root: str) -> dict:
    """Classify a Hebrew root by orthographic behaviour.

    Returns a dict with keys:
      guttural, initial_nun, contains_yod_vav, final_he, hollow,
      geminate, quadriliteral, irregular
    """
    letters = _parse_root(root)
    if not letters:
        return {
            "guttural": False,
            "initial_nun": False,
            "contains_yod_vav": False,
            "final_he": False,
            "hollow": False,
            "geminate": False,
            "quadriliteral": False,
            "irregular": False,
        }

    final_he = letters[-1] == "ה" if letters else False
    # Final ה roots are a separate weak-root class; do not count the final ה as a guttural.
    guttural_check = letters[:-1] if final_he else letters
    return {
        "guttural": any(c in GUTTURAL for c in guttural_check),
        "initial_nun": letters[0] == "נ" if letters else False,
        "contains_yod_vav": any(c in "וי" for c in letters),
        "final_he": final_he,
        "hollow": len(letters) >= 3 and letters[1] in "וי",
        "geminate": len(letters) >= 3
        and (letters[0] == letters[1] or letters[1] == letters[2] or letters[0] == letters[2]),
        "quadriliteral": len(letters) >= 4,
        "irregular": tuple(letters) in IRREGULAR_ROOTS or len(letters) not in (3, 4),
    }


def spelling_variants(vocalized: str, canonical: str, root_class: dict) -> dict:
    """Return the full, defective, common nonstandard and rejected spellings.

    * ``full`` is the standard plene spelling (matres inserted where implied).
    * ``defective`` is the spelling exactly as the vocalised input is stripped.
    * ``common_nonstandard`` lists common real-world alternatives.
    * ``rejected`` lists spellings that violate the root/form rules.
    """
    full = standard_unvocalized(vocalized)
    defective = strip_niqqud(vocalized)
    common_nonstandard: list[str] = []
    rejected: list[str] = []

    if full != defective:
        if canonical == full:
            common_nonstandard.append(defective)
        elif canonical == defective:
            common_nonstandard.append(full)
        else:
            common_nonstandard.extend([full, defective])

    # Swap a mater for the wrong vowel letter is generally rejected, unless the
    # root itself contains ו/י as a radical.
    if not root_class.get("contains_yod_vav"):
        if "ו" in canonical:
            yod_version = canonical.replace("ו", "י", 1)
            if yod_version not in (full, defective, canonical):
                rejected.append(yod_version)
        if "י" in canonical:
            vav_version = canonical.replace("י", "ו", 1)
            if vav_version not in (full, defective, canonical):
                rejected.append(vav_version)

    # A doubled mater is normally nonstandard/rejected.
    if "ו" in canonical:
        for i, ch in enumerate(canonical):
            if ch == "ו":
                doubled = canonical[: i + 1] + "ו" + canonical[i + 1 :]
                if doubled not in (full, defective, canonical):
                    rejected.append(doubled)
                    break

    common_nonstandard = [v for v in common_nonstandard if v and v != canonical]
    rejected = [v for v in rejected if v and v != canonical and v not in (full, defective)]

    return {
        "full": full,
        "defective": defective,
        "common_nonstandard": common_nonstandard,
        "rejected": rejected,
    }


def canonical_unvocalized(
    vocalized: str,
    root: str = "",
    binyan: str = "",
    form_key: str = "",
) -> dict:
    """Return the canonical unvocalised spelling of a Hebrew verb form.

    The returned dict has keys:
      spelling, class, rule_trace, confidence, unresolved, variants
    """
    normalized = normalize_unicode(vocalized)
    root_class = classify_root_orthographic_class(root)
    form_ctx = _form_context(form_key)
    clusters = _letter_clusters(normalized)
    trace: list[str] = [
        "normalize_unicode",
        f"root={root}",
        f"binyan={binyan}",
        f"form_key={form_key}",
        f"root_class={root_class}",
    ]

    result: list[str] = []
    unresolved = False
    n = len(clusters)

    for idx, (letter, marks, is_last) in enumerate(clusters):
        result.append(letter)
        if letter in VOWEL_MATERS or not marks or is_last:
            continue

        has_holam = HOLAM in marks
        has_qubuts = QUBUTS in marks
        if not (has_holam or has_qubuts):
            continue

        # If the vowel point is already represented by an explicit ו/י, keep it.
        if idx + 1 < n and clusters[idx + 1][0] in VOWEL_MATERS:
            trace.append(f"explicit_mater_after_{letter}")
            continue

        if has_qubuts:
            decision = _qubuts_decision(letter, idx, clusters, trace)
        else:
            decision = _holam_decision(letter, idx, clusters, root, root_class, form_ctx, trace)

        if decision == "insert":
            result.append("ו")
        elif decision in ("forbidden", "optional"):
            unresolved = True
            # In both cases we leave the spelling defective (no inserted mater);
            # the full variant is reported separately.

    spelling = strip_niqqud("".join(result))

    # Confidence: 1.0 when we reproduce the existing heuristic for known good
    # forms; 0.9 for rule-based canonical; 0.5 when unresolved.
    standard = standard_unvocalized(normalized)
    if not unresolved and spelling == standard:
        confidence = 1.0
    elif not unresolved:
        confidence = 0.9
    else:
        confidence = 0.5

    cls = "unresolved" if unresolved else "canonical"
    variants = spelling_variants(normalized, spelling, root_class)

    return {
        "spelling": spelling,
        "class": cls,
        "rule_trace": trace,
        "confidence": confidence,
        "unresolved": unresolved,
        "variants": variants,
    }
