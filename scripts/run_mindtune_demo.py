"""One-command launcher for the MindTune Research Console demo.

Usage:
    python scripts/run_mindtune_demo.py [--no-browser] [--production] [--verbose]
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV = REPO_ROOT / ".venv"
PYTHON = VENV / "bin" / "python"
API_MODULE = "mindtune_clm.api.app:create_app"
FRONT_DIR = REPO_ROOT / "apps" / "research-console"
DEMO_DATA = REPO_ROOT / "data" / "clm09b_demo"

API_HOST = "127.0.0.1"
API_PORT = 8000
FRONT_PORT = 5173

_API_URL = f"http://{API_HOST}:{API_PORT}"
_FRONT_URL = f"http://{API_HOST}:{FRONT_PORT}"


class LauncherError(Exception):
    """Fatal launcher error with a concise user-facing message."""


def log(message: str) -> None:
    print(f"[mindtune-demo] {message}", flush=True)


def _run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise


def validate_python_env() -> None:
    if not PYTHON.exists():
        raise LauncherError(
            "Python virtual environment not found at .venv. "
            "Create it and install dependencies first."
        )
    _run([str(PYTHON), "-c", "import mindtune_clm, uvicorn, fastapi; print('ok')"])


def validate_node_env() -> None:
    for binary in ["node", "npm"]:
        try:
            _run([binary, "--version"])
        except FileNotFoundError as exc:
            raise LauncherError(f"'{binary}' is not installed or not on PATH.") from exc


def ensure_node_modules() -> None:
    if (FRONT_DIR / "node_modules").exists():
        return
    log("Installing frontend dependencies (this may take a minute)...")
    _run(["npm", "install"], cwd=FRONT_DIR)


def _is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def _wait_for_url(url: str, timeout_s: float = 30.0, expected_status: int | None = None) -> None:
    deadline = time.time() + timeout_s
    last_error = ""
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if expected_status is None or resp.status == expected_status:
                    return
        except urllib.error.HTTPError:
            pass
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
        time.sleep(0.5)
    raise LauncherError(f"Timed out waiting for {url}: {last_error}")


def _http(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    url = f"{_API_URL}/api/v1{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        if not raw:
            return None
        return json.loads(raw.decode())


def _prepare_environment(production: bool) -> dict[str, str]:
    env = os.environ.copy()
    env["CLM05_API_HOST"] = API_HOST
    env["CLM05_API_PORT"] = str(API_PORT)
    env["CLM05_STORE_PATH"] = str(DEMO_DATA)
    env["CLM05_CORS_ORIGINS"] = (
        "http://127.0.0.1:5173,http://localhost:5173,"
        "http://127.0.0.1:8000,http://localhost:8000"
    )
    env["CLM05_CSP_ENABLED"] = "false"
    env["VITE_API_BASE"] = (
        "http://127.0.0.1:8000/api/v1" if production else "/api/v1"
    )
    return env


class DemoLauncher:
    def __init__(self, no_browser: bool, production: bool, verbose: bool) -> None:
        self.no_browser = no_browser
        self.production = production
        self.verbose = verbose
        self.api_proc: subprocess.Popen | None = None
        self.front_proc: subprocess.Popen | None = None

    def _popen(self, cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.Popen:
        if self.verbose:
            log(f"Starting: {' '.join(cmd)} (cwd={cwd or REPO_ROOT})")
        return subprocess.Popen(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )

    def _start_api(self) -> None:
        if not _is_port_free(API_HOST, API_PORT):
            raise LauncherError(f"Port {API_PORT} is already in use.")
        DEMO_DATA.mkdir(parents=True, exist_ok=True)
        env = _prepare_environment(self.production)
        cmd = [
            str(PYTHON), "-m", "uvicorn", API_MODULE, "--factory",
            "--host", API_HOST, "--port", str(API_PORT),
        ]
        self.api_proc = self._popen(cmd, cwd=REPO_ROOT, env=env)

    def _start_frontend(self) -> None:
        if not _is_port_free(API_HOST, FRONT_PORT):
            raise LauncherError(f"Port {FRONT_PORT} is already in use.")
        env = _prepare_environment(self.production)
        if self.production:
            log("Building production frontend...")
            build = subprocess.run(
                ["npm", "run", "build"],
                cwd=FRONT_DIR,
                env=env,
                text=True,
                capture_output=True,
            )
            if build.returncode != 0:
                print(build.stdout)
                print(build.stderr, file=sys.stderr)
                raise LauncherError("Frontend build failed.")
            cmd = ["npx", "vite", "preview", "--host", API_HOST, "--port", str(FRONT_PORT)]
        else:
            cmd = ["npm", "run", "dev"]
        self.front_proc = self._popen(cmd, cwd=FRONT_DIR, env=env)

    def _wait_for_api(self) -> None:
        _wait_for_url(f"{_API_URL}/api/v1/health/live", timeout_s=30.0)
        _wait_for_url(f"{_API_URL}/api/v1/health", timeout_s=30.0)
        log("API is ready.")

    def _wait_for_frontend(self) -> None:
        _wait_for_url(_FRONT_URL, timeout_s=60.0)
        log("Research Console is ready.")

    def _seed_demo(self) -> None:
        log("Seeding demo fixtures...")

        exp = _http(
            "POST",
            "/experiments",
            {
                "name": "CLM-09B Demo Hebrew Adaptive",
                "protocol_version_id": "clm-05-experimental.v1",
                "parameters": {
                    "objective": "Hebrew adaptive CLM instruction with Aaron/Giuseppe audio",
                    "curriculum_version": "clm06-hebrew-v1",
                    "calibration_required": True,
                    "primary_language": "Hebrew",
                    "voice": "Aaron",
                },
            },
        )
        exp_id = exp["id"]

        # Completed replay session for review/exports (must finish first to release playback lock).
        replay = _http(
            "POST",
            "/sessions",
            {
                "experiment_id": exp_id,
                "learner_id": "p-demo-01",
                "mode": "replay",
                "protocol_version_id": "clm-05-experimental.v1",
                "parameters": {
                    "sensor_source": "replay",
                    "stimulus_set": "default",
                    "playback_backend": "deterministic",
                    "notes": "Completed replay demo session",
                },
            },
        )
        replay_id = replay["id"]
        _http("POST", f"/sessions/{replay_id}/control", {"command": "prepare"})
        _http("POST", f"/sessions/{replay_id}/control", {"command": "start"})
        _http("POST", f"/sessions/{replay_id}/control", {"command": "step"})
        _http("POST", f"/sessions/{replay_id}/control", {"command": "stop"})

        # Synthetic-live session (kept running for the live view).
        live = _http(
            "POST",
            "/sessions",
            {
                "experiment_id": exp_id,
                "learner_id": "p-demo-01",
                "mode": "synthetic",
                "protocol_version_id": "clm-05-experimental.v1",
                "parameters": {
                    "sensor_source": "synthetic",
                    "stimulus_set": "default",
                    "playback_backend": "deterministic",
                    "notes": "Synthetic live demo session",
                },
            },
        )
        live_id = live["id"]
        _http("POST", f"/sessions/{live_id}/control", {"command": "prepare"})
        _http("POST", f"/sessions/{live_id}/control", {"command": "start"})
        _http("POST", f"/sessions/{live_id}/control", {"command": "step"})

        # Sensor registration.
        sensor = _http(
            "POST",
            "/sensors",
            {"sensor_id": "synth-fc11-01", "sensor_type": "synthetic"},
        )
        sensor_id = sensor["sensor_id"]
        _http("POST", f"/sensors/{sensor_id}/connect", {"session_id": live_id})

        # Hebrew adaptive session with one submitted response.
        heb = _http("POST", "/hebrew/sessions", {"learner_id": "p-demo-01", "parameters": {"max_trials": 20}})
        heb_id = heb["session_id"]
        trial = _http("GET", f"/sessions/{heb_id}/trials/current")
        if trial and trial.get("trial_id"):
            _http(
                "POST",
                f"/sessions/{heb_id}/trials/{trial['trial_id']}/response",
                {
                    "response_text": trial["expected"],
                    "response_time_ms": 1200,
                    "confidence": 5,
                },
            )

        # Calibration profile.
        cal = _http(
            "POST",
            "/calibrations",
            {
                "participant_id": "p-demo-01",
                "sensor_family": "fc11",
                "sensor_config_fingerprint": "fc11.default",
                "parser_version": "fc11.parser.v1",
                "feature_schema_version": "clm07.schema.v1",
            },
        )
        cal_id = cal["session_id"]
        _http("POST", f"/calibrations/{cal_id}/prepare", {})
        _http("POST", f"/calibrations/{cal_id}/start", {})
        _http("POST", f"/calibrations/{cal_id}/stop", {})

        # Scientific validation: study, assignment, analysis.
        study = _http(
            "POST",
            "/studies",
            {
                "title": "CLM-09B Demo Adaptive vs Fixed",
                "research_question": "Does adaptive CLM instruction improve immediate Hebrew recall?",
            },
        )
        study_id = study["study_id"]
        _http("POST", f"/studies/{study_id}/validate", {})
        _http(
            "POST",
            f"/studies/{study_id}/assignments",
            {"participant_ids": ["p-demo-01"], "seed": 42},
        )
        _http(
            "POST",
            f"/studies/{study_id}/analyses",
            {"hypothesis_id": "h1-adaptive-fixed", "seed": 123},
        )

        # Export for the replay session.
        _http(
            "POST",
            f"/sessions/{replay_id}/exports",
            {"format": "json"},
        )

        log("Demo fixtures seeded.")

    def _open_browser(self) -> None:
        if self.no_browser:
            return
        try:
            webbrowser.open(_FRONT_URL)
            log(f"Opened browser at {_FRONT_URL}")
        except Exception as exc:  # noqa: BLE001
            log(f"Could not open browser: {exc}")

    def _shutdown(self, *_args: Any) -> None:
        log("Shutting down...")
        for proc in (self.front_proc, self.api_proc):
            if proc is not None and proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    proc.terminate()
        for proc in (self.front_proc, self.api_proc):
            if proc is not None and proc.poll() is None:
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        proc.kill()
                    proc.wait(timeout=5)
        log("Stopped.")
        sys.exit(0)

    def run(self) -> int:
        try:
            validate_python_env()
            validate_node_env()
            ensure_node_modules()

            log("Starting CLM API...")
            self._start_api()
            self._wait_for_api()

            log("Starting Research Console...")
            self._start_frontend()
            self._wait_for_frontend()

            self._seed_demo()
            self._open_browser()

            log(f"MindTune Research Console is running at {_FRONT_URL}")
            log("Press Ctrl+C to stop.")

            # Drain logs in the background so the console stays responsive.
            while True:
                for proc in (self.api_proc, self.front_proc):
                    if proc is not None and proc.poll() is None:
                        try:
                            line = proc.stdout.readline()  # type: ignore[arg-type]
                            if line and self.verbose:
                                print(line.rstrip())
                        except Exception:  # noqa: BLE001
                            pass
                time.sleep(0.1)
        except LauncherError as exc:
            log(f"ERROR: {exc}")
            self._shutdown()
            return 1
        except KeyboardInterrupt:
            self._shutdown()
            return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch the MindTune Research Console demo")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser")
    parser.add_argument("--production", action="store_true", help="Build and serve a production-style bundle")
    parser.add_argument("--verbose", action="store_true", help="Print API/frontend logs")
    args = parser.parse_args()

    launcher = DemoLauncher(
        no_browser=args.no_browser,
        production=args.production,
        verbose=args.verbose,
    )
    signal.signal(signal.SIGINT, launcher._shutdown)
    atexit.register(launcher._shutdown)
    return launcher.run()


if __name__ == "__main__":
    sys.exit(main())
