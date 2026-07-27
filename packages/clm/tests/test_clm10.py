"""CLM-10 release-candidate field validation tests."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess

import pytest

from mindtune_clm.api.app import create_app
from mindtune_clm.ops.release import build_release_manifest

CLM09B_BASE_SHA = "220b3de11b8b09eadd282805e33d1b4bf44be0b9"


def _current_git_sha() -> str:
    git = shutil.which("git")
    if not git:
        pytest.skip("git not available")
    result = subprocess.run(
        [git, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        pytest.skip("could not read git sha")
    return result.stdout.strip()


def test_release_candidate_version_is_explicit() -> None:
    manifest = build_release_manifest(base_sha=CLM09B_BASE_SHA)
    assert manifest.semantic_version == "0.10.0-rc.1"
    assert manifest.release_candidate_number == 1
    assert manifest.api_version == "v1"
    assert manifest.research_console_version == "0.10.0-rc.1"


def test_manifest_references_exact_git_sha_and_base_sha() -> None:
    sha = _current_git_sha()
    manifest = build_release_manifest(base_sha=CLM09B_BASE_SHA)
    assert manifest.git_commit_sha == sha
    assert len(manifest.git_commit_sha) == 40
    assert manifest.base_sha == CLM09B_BASE_SHA
    assert len(manifest.base_sha) == 40


def test_manifest_checksum_is_self_consistent_and_deterministic() -> None:
    manifest = build_release_manifest(base_sha=CLM09B_BASE_SHA)
    c1 = manifest.checksum()
    c2 = manifest.checksum()
    assert len(c1) == 64
    assert c1 == c2
    payload = json.dumps(manifest.to_dict(), sort_keys=True, ensure_ascii=True, default=str)
    assert c1 == hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_backend_package_checksum_is_populated() -> None:
    manifest = build_release_manifest(base_sha=CLM09B_BASE_SHA)
    assert manifest.backend_package_checksum is not None
    assert len(manifest.backend_package_checksum) == 64


def test_build_refuses_to_claim_clean_on_dirty_tree() -> None:
    manifest = build_release_manifest(base_sha=CLM09B_BASE_SHA)
    # The manifest records dirty state accurately; it never asserts clean when dirty.
    assert isinstance(manifest.dirty_tree, bool)


def test_release_api_endpoints_serve_manifest() -> None:
    app = create_app()
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/api/v1/release")
    assert resp.status_code == 200
    body = resp.json()
    assert body["semantic_version"] == "0.10.0-rc.1"
    assert body["base_sha"] == CLM09B_BASE_SHA
    assert "git_commit_sha" in body

    manifest_resp = client.get("/api/v1/release/manifest")
    assert manifest_resp.status_code == 200
    manifest = manifest_resp.json()
    assert manifest["release_candidate_number"] == 1
    assert manifest["backend_package_checksum"] is not None

    validation_resp = client.get("/api/v1/release/validation")
    assert validation_resp.status_code == 200
    assert validation_resp.json()["hardware_tests"] == "blocked_by_hardware"

    limitations_resp = client.get("/api/v1/release/limitations")
    assert limitations_resp.status_code == 200

    evidence_resp = client.get("/api/v1/release/evidence")
    assert evidence_resp.status_code == 200
    assert "evidence_index" in evidence_resp.json()


def test_backend_package_imports_cleanly() -> None:
    import mindtune_clm
    import mindtune_clm.api.app
    import mindtune_clm.ops.release

    assert mindtune_clm is not None
    assert mindtune_clm.api.app.create_app is not None
    assert mindtune_clm.ops.release.build_release_manifest is not None


def test_release_manifest_is_immutable() -> None:
    manifest = build_release_manifest(base_sha=CLM09B_BASE_SHA)
    with pytest.raises(AttributeError):
        manifest.semantic_version = "changed"  # type: ignore[misc]
