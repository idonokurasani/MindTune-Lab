#!/usr/bin/env python3
"""CLM-10 release-candidate build and validation orchestrator."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = REPO_ROOT / "release" / "0.10.0-rc.1"
FRONTEND_DIR = REPO_ROOT / "apps" / "research-console"
PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
BASE_REMOTE_SHA = "220b3de11b8b09eadd282805e33d1b4bf44be0b9"

RESULTS: dict[str, Any] = {"started_at": datetime.now(timezone.utc).isoformat(), "gates": []}


def log(message: str) -> None:
    print(f"[build-release] {message}", flush=True)


def run(
    cmd: list[str] | str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    if isinstance(cmd, str):
        cmd_list = ["/bin/sh", "-c", cmd]
        shell = True
    else:
        cmd_list = [str(c) for c in cmd]
        shell = False
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    log(f"Running: {' '.join(cmd_list) if not shell else cmd}")
    try:
        proc = subprocess.run(
            cmd_list,
            cwd=cwd or REPO_ROOT,
            env=merged_env,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "returncode": -1,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "error": f"timeout after {timeout}s",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "command": cmd,
            "returncode": -2,
            "stdout": "",
            "stderr": str(exc),
            "error": str(exc),
        }
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def add_gate(name: str, passed: bool, details: dict[str, Any] | None = None) -> None:
    RESULTS["gates"].append({"name": name, "passed": passed, "details": details or {}})


def check_branch() -> bool:
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    actual_branch = branch["stdout"].strip()
    if actual_branch != "feat/clm-10-release-candidate-field-validation":
        log(f"WARNING: branch is {actual_branch}, expected feat/clm-10-release-candidate-field-validation")
    sha = run(["git", "rev-parse", "HEAD"])
    log(f"Git branch: {actual_branch}, SHA: {sha['stdout'].strip()}")
    return actual_branch == "feat/clm-10-release-candidate-field-validation"


def check_dirty(allow_dirty: bool) -> bool:
    status = run(["git", "status", "--porcelain"])
    dirty = bool(status["stdout"].strip())
    if dirty and not allow_dirty:
        log("ERROR: dirty tree and --allow-dirty not set")
        return False
    log(f"Dirty tree: {dirty}")
    return True


def parse_validation_matrix(md_path: Path) -> list[dict[str, str]]:
    text = md_path.read_text(encoding="utf-8")
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for line in text.splitlines():
        parts = [c.strip() for c in line.split("|")]
        parts = [c for c in parts if c]
        if not parts:
            continue
        if "Capability ID" in parts[0]:
            headers = parts
            continue
        if set(parts[0]) <= set("- "):
            continue
        if not headers:
            continue
        rows.append({headers[i]: parts[i] for i in range(min(len(headers), len(parts)))})
    return rows


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def checksum_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checksums_in_dir(directory: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            rel = path.relative_to(directory).as_posix()
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def build_release_notes(manifest_checksum: str) -> str:
    return f"""# Release Notes — MindTune Lab 0.10.0-rc.1

- Release candidate for CLM-10 integrated field validation.
- Built from branch `feat/clm-10-release-candidate-field-validation`.
- Base SHA: `{BASE_REMOTE_SHA}`.
- Adds release-candidate manifest API and Research Console page.
- Records all known limitations and go/no-go gates.
- Manifest checksum: `{manifest_checksum}`.

See `CLM_10_KNOWN_LIMITATIONS.md` and `CLM_10_GO_NO_GO.md`.
"""


def build_installation() -> str:
    return """# Installation — MindTune Lab 0.10.0-rc.1

## Python backend

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Hebrew domain (optional)

Use Python 3.12 and the `.venv_phonikud` environment, or install `pip install -e ".[hebrew]"`.

## Research Console frontend

```bash
cd apps/research-console
npm ci
npm run build
```

## Launch

```bash
python scripts/run_mindtune_demo.py --production
```

Open the URL printed by the launcher.
"""


def build_evidence_index() -> str:
    return """# Evidence Index

Indexed evidence for CLM-10 is stored under `docs/release/evidence/clm-10/`.
This file is generated by `scripts/build_release_candidate.py`.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the CLM-10 release candidate.")
    parser.add_argument("--allow-dirty", action="store_true", help="allow dirty git tree")
    parser.add_argument("--skip-frontend-e2e", action="store_true", default=True, help="skip Playwright E2E tests")
    parser.add_argument("--skip-container", action="store_true", default=True, help="skip Docker build")
    parser.add_argument("--base-sha", default=BASE_REMOTE_SHA, help="CLM-09B base SHA")
    args = parser.parse_args()

    os.environ.setdefault("CLM10_BASE_SHA", args.base_sha)
    os.environ.setdefault("PYTHONPATH", str(REPO_ROOT))

    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    evidence_dir = REPO_ROOT / "docs" / "release" / "evidence" / "clm-10"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    log(f"Release target: {RELEASE_DIR}")

    passed = True

    if not check_branch():
        passed = False
        add_gate("branch_check", False, {"warning": "branch mismatch"})
    else:
        add_gate("branch_check", True)

    if not check_dirty(args.allow_dirty):
        passed = False
        add_gate("dirty_tree", False, {"message": "dirty tree not allowed"})
    else:
        add_gate("dirty_tree", True)

    # Backend lint
    ruff = run([str(PYTHON), "-m", "ruff", "check", "packages/clm/src/mindtune_clm/", "packages/clm/tests/", "packages/mpe/src/mpe/"])
    ruff_ok = ruff["returncode"] == 0
    passed = passed and ruff_ok
    add_gate("ruff", ruff_ok, {"returncode": ruff["returncode"], "summary": (ruff["stdout"].splitlines() or ["ok"])[-5:]})

    # Backend type checks
    mypy_paths = [
        "packages/clm/src/mindtune_clm/ops",
        "packages/clm/src/mindtune_clm/validation",
        "packages/clm/src/mindtune_clm/calibration",
        "packages/clm/src/mindtune_clm/api",
        "packages/clm/src/mindtune_clm/live_loop",
        "packages/clm/src/mindtune_clm/live",
        "packages/clm/src/mindtune_clm/audio",
        "packages/clm/src/mindtune_clm/voice",
    ]
    mypy = run([str(PYTHON), "-m", "mypy", "--exclude", "hebrew/", *mypy_paths])
    mypy_ok = mypy["returncode"] == 0
    passed = passed and mypy_ok
    add_gate("mypy", mypy_ok, {"returncode": mypy["returncode"], "summary": (mypy["stdout"].splitlines() or ["ok"])[-10:]})

    # CLM tests (focus on CLM-10 and then full suite)
    clm10 = run([str(PYTHON), "-m", "pytest", "packages/clm/tests/test_clm10.py", "-v"], timeout=180)
    clm10_ok = clm10["returncode"] == 0
    passed = passed and clm10_ok
    add_gate("pytest_clm10", clm10_ok, {"returncode": clm10["returncode"], "summary": (clm10["stdout"].splitlines() or ["ok"])[-20:]})

    clm_all = run([str(PYTHON), "-m", "pytest", "packages/clm/tests", "-q"], timeout=300)
    clm_all_ok = clm_all["returncode"] == 0
    passed = passed and clm_all_ok
    add_gate("pytest_clm_all", clm_all_ok, {"returncode": clm_all["returncode"]})

    mpe_all = run([str(PYTHON), "-m", "pytest", "packages/mpe/tests", "-q"], timeout=300)
    mpe_all_ok = mpe_all["returncode"] == 0
    passed = passed and mpe_all_ok
    add_gate("pytest_mpe_all", mpe_all_ok, {"returncode": mpe_all["returncode"]})

    # Frontend install (skip if already present)
    if not (FRONTEND_DIR / "node_modules").exists():
        npm_install = run(["npm", "ci"], cwd=FRONTEND_DIR, timeout=120)
    else:
        npm_install = {"returncode": 0, "stdout": "node_modules present"}
    npm_install_ok = npm_install["returncode"] == 0
    passed = passed and npm_install_ok
    add_gate("npm_install", npm_install_ok, {"returncode": npm_install["returncode"]})

    front_env = os.environ.copy()
    front_env["VITE_API_BASE"] = "http://127.0.0.1:8000/api/v1"
    front_lint = run(["npm", "run", "lint"], cwd=FRONTEND_DIR, env=front_env, timeout=120)
    front_lint_ok = front_lint["returncode"] == 0
    passed = passed and front_lint_ok
    add_gate("frontend_lint", front_lint_ok, {"returncode": front_lint["returncode"]})

    front_test = run(["npm", "run", "test"], cwd=FRONTEND_DIR, env=front_env, timeout=120)
    front_test_ok = front_test["returncode"] == 0
    passed = passed and front_test_ok
    add_gate("frontend_test", front_test_ok, {"returncode": front_test["returncode"]})

    front_build = run(["npm", "run", "build"], cwd=FRONTEND_DIR, env=front_env, timeout=180)
    front_build_ok = front_build["returncode"] == 0
    passed = passed and front_build_ok
    add_gate("frontend_build", front_build_ok, {"returncode": front_build["returncode"]})

    if not args.skip_frontend_e2e:
        e2e = run(["npm", "run", "test:e2e"], cwd=FRONTEND_DIR, env=front_env, timeout=300)
        add_gate("frontend_e2e", e2e["returncode"] == 0, {"returncode": e2e["returncode"], "status": "optional"})

    # Build Python package
    build = run([str(PYTHON), "-m", "build"])
    build_ok = build["returncode"] == 0
    add_gate("python_build", build_ok, {"returncode": build["returncode"], "status": "optional"})

    # Container build (optional)
    if not args.skip_container and shutil.which("docker"):
        docker = run(["docker", "build", "-t", "mindtune:0.10.0-rc.1", "."], timeout=300)
        add_gate("container_build", docker["returncode"] == 0, {"returncode": docker["returncode"], "status": "optional"})

    # Generate manifest
    from mindtune_clm.ops.release import build_release_manifest

    manifest = build_release_manifest(
        release_id="mindtune-lab-0.10.0-rc.1",
        base_sha=args.base_sha,
        container_image_digest=None,
    )
    manifest_path = RELEASE_DIR / "RELEASE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, default=str), encoding="utf-8")
    manifest_checksum = manifest.checksum()

    # Copy / generate release docs
    (RELEASE_DIR / "RELEASE_NOTES.md").write_text(build_release_notes(manifest_checksum), encoding="utf-8")
    (RELEASE_DIR / "INSTALLATION.md").write_text(build_installation(), encoding="utf-8")
    shutil.copy(REPO_ROOT / "docs" / "release" / "CLM_10_KNOWN_LIMITATIONS.md", RELEASE_DIR / "KNOWN_LIMITATIONS.md")
    shutil.copy(REPO_ROOT / "docs" / "release" / "CLM_10_VALIDATION_MATRIX.md", RELEASE_DIR / "VALIDATION_MATRIX.md")
    shutil.copy(REPO_ROOT / "docs" / "release" / "CLM_10_GO_NO_GO.md", RELEASE_DIR / "GO_NO_GO.md")
    (RELEASE_DIR / "EVIDENCE_INDEX.md").write_text(build_evidence_index(), encoding="utf-8")

    matrix_rows = parse_validation_matrix(RELEASE_DIR / "VALIDATION_MATRIX.md")
    write_csv(matrix_rows, RELEASE_DIR / "VALIDATION_MATRIX.csv")

    # Test results
    RESULTS["finished_at"] = datetime.now(timezone.utc).isoformat()
    RESULTS["manifest_path"] = str(manifest_path.relative_to(REPO_ROOT))
    RESULTS["manifest_checksum"] = manifest_checksum
    RESULTS["release_id"] = manifest.release_id
    (RELEASE_DIR / "TEST_RESULTS.json").write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")

    # Checksums
    release_checksums = checksums_in_dir(RELEASE_DIR)
    (RELEASE_DIR / "CHECKSUMS.sha256").write_text(
        "\n".join(f"{sha}  {rel}" for rel, sha in release_checksums.items()) + "\n",
        encoding="utf-8",
    )

    # Evidence index files
    (evidence_dir / "README.md").write_text(build_evidence_index(), encoding="utf-8")

    log(f"Manifest: {manifest_path}")
    log(f"Manifest checksum: {manifest_checksum}")
    log(f"Overall result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
