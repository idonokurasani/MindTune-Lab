"""One-shot ingestion pipeline for all shared Hebrew resources."""

from __future__ import annotations

from pathlib import Path

from .adapters.phonikud_adapter import phonemize
from .resources.eran_tomer import ingest as ingest_eran_tomer
from .resources.svlm import ingest as ingest_svlm
from .resources.manifests import merge_manifests


def main() -> int:
    base = Path(__file__).resolve().parents[1] / "data" / "hebrew"

    # Eran Tomer
    eran_manifest = ingest_eran_tomer(
        resource_dir=base / "resources" / "eran_tomer",
        output_dir=base / "indexes" / "eran_tomer",
    )

    # SVLM (optionally phonemized; skip by default to keep ingestion fast)
    svlm_manifest = ingest_svlm(
        resource_dir=base / "resources" / "svlm",
        output_dir=base / "indexes" / "svlm",
        phonikud_fn=phonemize,
    )

    # Merge manifests
    merged = merge_manifests([eran_manifest, svlm_manifest])
    manifests_dir = base / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    (manifests_dir / "hebrew_resources_manifest.json").write_text(
        __import__("json").dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Ingested Eran Tomer: {eran_manifest}")
    print(f"Ingested SVLM: {svlm_manifest}")
    print(f"Merged manifest: {manifests_dir / 'hebrew_resources_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
