"""Ingest and index the SVLM Hebrew Wikipedia Corpus."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..normalization import normalize_hebrew, strip_niqqud


@dataclass
class SVLMSentence:
    sentence_id: str
    original_hebrew: str
    normalized_hebrew: str
    token_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def tokenize(text: str) -> list[str]:
    """Simple Hebrew tokenization: split on whitespace and punctuation."""
    return re.findall(r"[\u0590-\u05fe]+", text)


def ingest(
    resource_dir: Path,
    output_dir: Path,
    phonikud_fn: Any | None = None,
) -> Path:
    """Ingest SVLM corpus, build indexes and optional phoneme coverage."""
    output_dir.mkdir(parents=True, exist_ok=True)
    corpus_file = resource_dir / "SVLM_Hebrew_Wikipedia_Corpus.txt"

    sentences: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    by_length: dict[int, list[int]] = defaultdict(list)
    by_token_count: dict[int, list[int]] = defaultdict(list)
    by_lemma_surface: dict[str, list[int]] = defaultdict(list)

    with corpus_file.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                normalized = normalize_hebrew(line)
                tokens = tokenize(normalized)
                record = {
                    "sentence_id": f"svlm-{idx:07d}",
                    "original_hebrew": line,
                    "normalized_hebrew": normalized,
                    "token_count": len(tokens),
                    "phonemes": "",
                    "phoneme_inventory": [],
                    "coverage_score": 0.0,
                    "complexity_score": float(len(tokens)),
                    "approved": False,
                    "source": "svlm",
                }
                if phonikud_fn:
                    try:
                        record["phonemes"] = phonikud_fn(normalized)
                        inventory = sorted(set(c for c in record["phonemes"] if c.isalpha()))
                        record["phoneme_inventory"] = inventory
                        record["coverage_score"] = len(inventory)
                    except Exception as exc:
                        record["phonemes_error"] = str(exc)
                sentences.append(record)
                by_length[len(normalized)].append(len(sentences) - 1)
                by_token_count[len(tokens)].append(len(sentences) - 1)
                for t in tokens:
                    by_lemma_surface[strip_niqqud(t)].append(len(sentences) - 1)
            except Exception as exc:
                rejected.append({"line": idx, "reason": str(exc)})

    (output_dir / "sentences.json").write_text(
        json.dumps(sentences, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    indexes = {
        "by_length": dict(by_length),
        "by_token_count": dict(by_token_count),
        "by_surface": dict(by_lemma_surface),
    }
    (output_dir / "indexes.json").write_text(
        json.dumps(indexes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "rejected.json").write_text(
        json.dumps(rejected, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manifest = {
        "resource_name": "svlm_hebrew_wikipedia_corpus",
        "upstream_url": "https://github.com/NLPH/SVLM-Hebrew-Wikipedia-Corpus",
        "version_or_commit": "unknown",
        "license": "CC-BY-SA 3.0",
        "import_date": datetime.now(timezone.utc).isoformat(),
        "file_hashes": {"SVLM_Hebrew_Wikipedia_Corpus.txt": _sha256(corpus_file)},
        "total_records": len(sentences) + len(rejected),
        "accepted_records": len(sentences),
        "rejected_records": len(rejected),
        "normalization_rules": ["NFC normalization", "maqaf replacement", "whitespace collapse"],
        "parser_version": "hebrew.resources.svlm.v1",
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path
