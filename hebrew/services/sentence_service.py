"""SVLM sentence and example service with safety checks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..approval import ApprovalPipeline
from ..models import ExampleSentence
from ..normalization import strip_niqqud
from ..usage import classify_sentence


class SentenceService:
    """Search, filter and rank SVLM corpus sentences.

    Sentence candidates are never auto-approved; they remain
    `curriculum_status: not_reviewed` until an explicit reviewer action.
    """

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or (Path(__file__).resolve().parents[2] / "data" / "hebrew")
        self.sentences: list[dict[str, Any]] = []
        self.indexes: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        sentences_path = self.data_dir / "indexes" / "svlm" / "sentences.json"
        indexes_path = self.data_dir / "indexes" / "svlm" / "indexes.json"
        if sentences_path.exists():
            self.sentences = json.loads(sentences_path.read_text(encoding="utf-8"))
        if indexes_path.exists():
            self.indexes = json.loads(indexes_path.read_text(encoding="utf-8"))

    def _analyze(self, sentence: ExampleSentence) -> ExampleSentence:
        """Populate target-form checks and quality heuristics."""
        target = sentence.target_form or ""
        normalized = sentence.normalized_hebrew

        # Target form presence
        sentence.target_form_present = bool(target) and target in normalized
        sentence.target_form_exact_match = bool(target) and normalized == target
        sentence.target_form_morphological_match = bool(target) and strip_niqqud(
            target
        ) in strip_niqqud(normalized)

        # Punctuation / noise
        latin_ratio = len(re.findall(r"[A-Za-z]", normalized)) / max(len(normalized), 1)
        digit_ratio = len(re.findall(r"\d", normalized)) / max(len(normalized), 1)
        weird_chars = len(re.findall(r"[^\u0590-\u05fe\s\d\-.'!?\"'()\[\]{}:;]", normalized))

        sentence.punctuation_quality_ok = (
            normalized.endswith((".", "!", "?", '"', "'", ":", ";")) or normalized[-1].isalpha()
            if normalized
            else False
        ) and weird_chars < 3
        sentence.suspected_noise = latin_ratio > 0.3 or digit_ratio > 0.2 or weird_chars > 3

        # Complexity / ambiguity
        unique_tokens = len(set(re.findall(r"[\u0590-\u05fe]+", normalized)))
        sentence.vocabulary_complexity = float(unique_tokens) / max(sentence.token_count, 1)
        sentence.ambiguity_score = sentence.vocabulary_complexity

        # Source eligibility
        sentence.source_id = "svlm"
        sentence.source_eligibility = "private_research_only"
        sentence.licensing_eligibility = "private_research_only"

        # Usage and approval
        sentence.curriculum_suitability = classify_sentence(sentence)
        ApprovalPipeline().evaluate_sentence(sentence)
        return sentence

    def lookup(
        self,
        lemma: str | None = None,
        min_tokens: int | None = None,
        max_tokens: int | None = None,
        max_length: int | None = None,
        target_form: str | None = None,
        limit: int = 10,
    ) -> list[ExampleSentence]:
        """Return candidate sentences filtered by lemma and complexity."""
        results: list[ExampleSentence] = []
        target_plain = strip_niqqud(lemma) if lemma else None

        for s in self.sentences:
            data = {**s}
            # SVLM sentences.json uses the legacy 'source' field name.
            data["source_id"] = data.pop("source", "svlm")
            sentence = ExampleSentence(**data)
            sentence.target_form = target_form or lemma or ""
            self._analyze(sentence)
            if target_plain and target_plain not in sentence.normalized_hebrew:
                continue
            if min_tokens is not None and sentence.token_count < min_tokens:
                continue
            if max_tokens is not None and sentence.token_count > max_tokens:
                continue
            if max_length is not None and len(sentence.normalized_hebrew) > max_length:
                continue
            if sentence.curriculum_status == "rejected":
                continue
            results.append(sentence)
            if len(results) >= limit:
                break
        return results

    def get_example_sentences(self, lemma_or_form: str, limit: int = 5) -> list[ExampleSentence]:
        return self.lookup(lemma=lemma_or_form, target_form=lemma_or_form, limit=limit)
