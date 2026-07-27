"""CLM-05 API state and service layer."""

from __future__ import annotations

import hashlib
import json
import queue
import re
import shutil
import tempfile
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, cast

from mindtune_clm.api.commands import ControlCommand, SensorCommand, SessionStatus
from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.errors import (
    CLM05APIError,
    IdempotencyConflictError,
    NotFoundError,
    ResourceLockedError,
    StateMachineError,
)
from mindtune_clm.audio.assets import AudioAssetRegistry
from mindtune_clm.audio.playback import PlaybackScheduler
from mindtune_clm.audio.renderer import AudioRenderer
from mindtune_clm.live.fc11 import FC11LiveSource
from mindtune_clm.live.gateway import LiveGateway
from mindtune_clm.live.source import SyntheticLiveSource
from mindtune_clm.live_loop.fixture_clm04b import (
    build_voice_cache_and_registry,
    make_synthetic_frames,
)
from mindtune_clm.live_loop.orchestrator import LiveClosedLoopOrchestrator
from mindtune_clm.live_loop.playback_backend import DeterministicPlaybackBackend
from mindtune_clm.live_loop.receipts import LiveLoopCycleReceipt
from mindtune_clm.voice.cache import VoiceCache
from mpe.event_store import EventStore, InMemoryEventStore
from mpe.events import Event
from mpe.persistence.store import SQLiteEventStore
from mpe.types import SessionID, make_id

_MAX_SSE_QUEUE = 10000


def _new_request_id() -> str:
    return str(uuid.uuid4())


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _payload_hash(payload: Any) -> str:
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _hash_redacted(data: dict[str, Any]) -> str:
    body = _stable_json(data)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _redact_string(value: str) -> str:
    if re.fullmatch(r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", value):
        return "[REDACTED_MAC]"
    if re.search(r"^(?:[A-Za-z]:[\\/]|/|[~]/)|(?:/[^/\s]+)+", value):
        return "[REDACTED_PATH]"
    return value


def _redact_payload(payload: Any, key: str | None = None) -> Any:
    if isinstance(payload, dict):
        result: dict[str, Any] = {}
        for k, v in payload.items():
            if k in {"learner_id", "participant_id", "token", "api_key", "password", "secret", "authorization"}:
                result["[REDACTED]"] = "[REDACTED]"
            else:
                result[k] = _redact_payload(v, key=k)
        return result
    if isinstance(payload, list):
        return [_redact_payload(i) for i in payload]
    if isinstance(payload, str):
        return _redact_string(payload)
    return payload


def _sanitize_event(event: Event) -> dict[str, Any]:
    data = event.as_dict()
    data["payload"] = _redact_payload(data.get("payload", {}))
    return cast(dict[str, Any], data)


def _export_events_json(events: list[Event]) -> str:
    return _stable_json([_sanitize_event(e) for e in events])


def _export_events_jsonl(events: list[Event]) -> str:
    lines = []
    for e in events:
        lines.append(_stable_json(_sanitize_event(e)))
    return "\n".join(lines) + ("\n" if lines else "")


class NotifyingEventStore:
    """Wraps an MPE event store and notifies a listener on every append."""

    def __init__(self, inner: EventStore, listener: Callable[[Event], None]) -> None:
        self.inner = inner
        self.listener = listener

    def append(self, event: Event, expected_version: int | None = None) -> None:
        self.inner.append(event, expected_version)
        self.listener(event)

    def read(
        self,
        session_id: SessionID,
        from_seq: int | None = None,
        to_seq: int | None = None,
    ):
        return self.inner.read(session_id, from_seq, to_seq)

    def get_last_sequence(self, session_id: SessionID):
        return self.inner.get_last_sequence(session_id)

    def all_events(self):
        return self.inner.all_events()

    def list_sessions(self):
        return self.inner.list_sessions()

    def close(self) -> None:
        self.inner.close()


@dataclass
class APISession:
    """Runtime state for one CLM-05 API session."""

    id: str
    experiment_id: str | None
    learner_id: str
    mode: str
    protocol_version_id: str
    parameters: dict[str, Any]
    cache_dir: Path | None
    store_path: Path | None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    status: str = SessionStatus.CREATED.value
    orchestrator: Any | None = None
    gateway: Any | None = None
    frames: list[Any] = field(default_factory=list)
    frame_index: int = 0
    sse_events: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=_MAX_SSE_QUEUE))
    sse_lock: threading.Lock = field(default_factory=threading.Lock)
    owned_locks: set[str] = field(default_factory=set)
    store: Any | None = None
    calibration_profile_id: str | None = None
    calibration_profile_version: str | None = None

    def on_event(self, event: Event) -> None:
        if str(event.session_id) != str(self.id):
            return
        with self.sse_lock:
            self.sse_events.append(event.as_dict())

    def response_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "learner_id": self.learner_id,
            "mode": self.mode,
            "status": self.status,
            "protocol_version_id": self.protocol_version_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "calibration_profile_id": self.calibration_profile_id,
            "calibration_profile_version": self.calibration_profile_version,
        }

    def close(self) -> None:
        if self.store is not None:
            try:
                self.store.close()
            except Exception:
                pass


class CLM05Service:
    """In-memory service layer holding experiments, sessions, sensors and locks."""

    def __init__(self, config: CLM05APIConfig) -> None:
        self.config = config
        self.accepting_mutations = True
        self.experiments: dict[str, dict[str, Any]] = {}
        self.sessions: dict[str, APISession] = {}
        self.sensors: dict[str, dict[str, Any]] = {}
        self.idempotency: dict[str, dict[str, Any]] = {}
        self.resource_locks: dict[str, str] = {}
        self._lock = threading.RLock()
        self._base_store_path = Path(config.store_path) if config.store_path else None
        self._protocols: list[dict[str, Any]] = [
            {"protocol_version_id": "clm-05-experimental.v1", "name": "CLM-05 Experimental API", "description": "Unified experimental control plane"},
            {"protocol_version_id": "clm-04b.v1.0.0", "name": "CLM-04B Live Closed Loop", "description": "Live FC11 + Giuseppe/Aaron closed-loop orchestrator"},
            {"protocol_version_id": "clm-04.v1.0.0", "name": "CLM-04 Live FC11 Gateway", "description": "Provider-neutral live sensor gateway"},
            {"protocol_version_id": "clm-03b.v1.0.0", "name": "CLM-03B SpeechGen Voice", "description": "Giuseppe/Aaron voice pipeline"},
        ]
        self._calibration_service: Any | None = None

    def _request_id(self) -> str:
        return _new_request_id()

    def set_calibration_service(self, service: Any | None) -> None:
        """Attach the CLM-07 calibration service for session profile selection."""
        self._calibration_service = service

    def _check_mutations(self) -> None:
        if not self.accepting_mutations:
            raise CLM05APIError(
                code="service_shutting_down",
                message="The API is not accepting mutations",
                status_code=503,
                request_id=self._request_id(),
                retryable=True,
            )

    def _idempotent(
        self,
        key: str | None,
        payload: Any,
        factory: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        if not key:
            return factory()
        phash = _payload_hash(payload)
        with self._lock:
            record = self.idempotency.get(key)
            if record is not None:
                if record["payload_hash"] != phash:
                    raise IdempotencyConflictError(key, request_id=self._request_id())
                return cast(dict[str, Any], record["response"])
            response: dict[str, Any] = factory()
            self.idempotency[key] = {
                "payload_hash": phash,
                "response": response,
                "created_at": time.time(),
            }
            return response

    def _create_store(self, session_id: str, on_event: Callable[[Event], None]) -> NotifyingEventStore:
        if self._base_store_path is not None:
            path = self._base_store_path / f"{session_id}.sqlite"
            path.parent.mkdir(parents=True, exist_ok=True)
            inner: EventStore = SQLiteEventStore(path)
        else:
            inner = InMemoryEventStore()
        return NotifyingEventStore(inner, on_event)

    def _acquire_lock(self, resource: str, owner: str) -> None:
        with self._lock:
            current = self.resource_locks.get(resource)
            if current is not None and current != owner:
                raise ResourceLockedError(resource, current, request_id=self._request_id())
            self.resource_locks[resource] = owner

    def _release_lock(self, resource: str, owner: str) -> None:
        with self._lock:
            if self.resource_locks.get(resource) == owner:
                del self.resource_locks[resource]

    def _release_owned_locks(self, session: APISession) -> None:
        for resource in list(session.owned_locks):
            self._release_lock(resource, session.id)
        session.owned_locks.clear()

    # ------------------------------------------------------------------ #
    # Experiments
    # ------------------------------------------------------------------ #

    def create_experiment(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._check_mutations()
        exp_id = str(uuid.uuid4())
        exp = {
            "id": exp_id,
            "name": payload.get("name", "untitled"),
            "protocol_version_id": payload.get("protocol_version_id"),
            "parameters": payload.get("parameters", {}),
            "created_at": time.time(),
        }
        with self._lock:
            self.experiments[exp_id] = exp
        return exp

    def get_experiment(self, experiment_id: str) -> dict[str, Any]:
        with self._lock:
            exp = self.experiments.get(experiment_id)
        if not exp:
            raise NotFoundError(experiment_id, request_id=self._request_id())
        return exp

    def list_experiments(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(e) for e in self.experiments.values()]

    def delete_experiment(self, experiment_id: str) -> dict[str, Any]:
        self._check_mutations()
        with self._lock:
            if experiment_id not in self.experiments:
                raise NotFoundError(experiment_id, request_id=self._request_id())
            del self.experiments[experiment_id]
        return {"deleted": True, "id": experiment_id}

    # ------------------------------------------------------------------ #
    # Protocols
    # ------------------------------------------------------------------ #

    def list_protocols(self) -> list[dict[str, Any]]:
        return [dict(p) for p in self._protocols]

    def get_protocol(self, protocol_version_id: str) -> dict[str, Any]:
        for p in self._protocols:
            if p["protocol_version_id"] == protocol_version_id:
                return dict(p)
        raise NotFoundError(protocol_version_id, request_id=self._request_id())

    # ------------------------------------------------------------------ #
    # Sessions
    # ------------------------------------------------------------------ #

    def _cache_dir_for(self, session_id: str) -> Path:
        if self._base_store_path is not None:
            base = self._base_store_path.parent / "clm05_cache" / session_id
        else:
            base = Path(tempfile.mkdtemp(prefix=f"clm05_cache_{session_id}_"))
        base.mkdir(parents=True, exist_ok=True)
        return base

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._check_mutations()

        def factory() -> dict[str, Any]:
            session_id = str(make_id(SessionID))
            cache_dir = self._cache_dir_for(session_id)
            store_path = (
                self._base_store_path / f"{session_id}.sqlite"
                if self._base_store_path is not None
                else None
            )
            if store_path is not None:
                store_path.parent.mkdir(parents=True, exist_ok=True)
            session = APISession(
                id=session_id,
                experiment_id=payload.get("experiment_id"),
                learner_id=payload.get("learner_id", "anonymous"),
                mode=payload.get("mode", "synthetic"),
                protocol_version_id=payload.get("protocol_version_id", "clm-05-experimental.v1"),
                parameters=payload.get("parameters", {}),
                cache_dir=cache_dir,
                store_path=store_path,
            )
            session.store = self._create_store(session_id, session.on_event)

            # Pin a calibration profile version at session creation when possible.
            if self._calibration_service is not None:
                params = payload.get("parameters", {})
                participant_id = params.get("participant_id") or session.learner_id
                profile_id, profile_version = self._calibration_service.select_profile_for_session(
                    participant_id=participant_id,
                    sensor_family=params.get("sensor_family", "fc11"),
                    sensor_config_fingerprint=params.get("sensor_config_fingerprint", "fc11.default"),
                    parser_version=params.get("parser_version", "fc11.parser.v1"),
                    feature_schema_version=params.get("feature_schema_version", "clm07.schema.v1"),
                    pinned_profile_id=params.get("calibration_profile_id"),
                )
                session.calibration_profile_id = profile_id
                session.calibration_profile_version = profile_version

            with self._lock:
                self.sessions[session_id] = session
            return session.response_dict()

        return self._idempotent(payload.get("idempotency_key"), payload, factory)

    def get_session(self, session_id: str) -> APISession:
        with self._lock:
            session = self.sessions.get(session_id)
        if not session:
            raise NotFoundError(session_id, request_id=self._request_id())
        return session

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._lock:
            return [s.response_dict() for s in self.sessions.values()]

    def _ensure_transition(self, session: APISession, allowed: set[str], target: str, action: str) -> None:
        if session.status not in allowed:
            raise StateMachineError(session.id, action, request_id=self._request_id())
        session.status = target
        session.updated_at = time.time()

    def _build_orchestrator(self, session: APISession) -> None:
        parameters = session.parameters
        skip_voice = bool(parameters.get("skip_voice_cache"))
        cache_dir = session.cache_dir
        if cache_dir is None:
            raise CLM05APIError(
                code="missing_cache_dir",
                message="Session cache directory not configured",
                status_code=500,
                request_id=self._request_id(),
                resource_id=session.id,
            )
        if skip_voice:
            cache: Any = VoiceCache(cache_dir / "empty")
            registry = AudioAssetRegistry()
        else:
            cache, registry = build_voice_cache_and_registry(cache_dir)

        backend = DeterministicPlaybackBackend()
        scheduler = PlaybackScheduler(
            backend=backend.play,
            backend_latency=0.0,
            safe_boundary="between_mantra_cycles",
        )
        renderer = AudioRenderer(asset_registry=registry)

        store = session.store
        orchestrator = LiveClosedLoopOrchestrator(
            store=store,
            cache=cache,
            asset_registry=registry,
            playback_backend=backend,
            scheduler=scheduler,
            renderer=renderer,
            protocol_version_id=session.protocol_version_id,
            learner_id=session.learner_id,
            session_id=SessionID(session.id),
        )
        session.orchestrator = orchestrator

        source: Any
        if session.mode == "live" and parameters.get("csv_text"):
            source = FC11LiveSource(parameters["csv_text"])
        else:
            source = SyntheticLiveSource(
                source_id=parameters.get("source_id", "synthetic"),
                duration=float(parameters.get("duration", 10.0)),
                packet_interval=float(parameters.get("packet_interval", 0.1)),
                seed=int(parameters.get("seed", 0)),
            )
        gateway = LiveGateway(source=source, store=store)
        session.gateway = gateway
        session.orchestrator.gateway = gateway

    def prepare_session(self, session_id: str) -> dict[str, Any]:
        self._check_mutations()
        session = self.get_session(session_id)
        if session.status not in {SessionStatus.CREATED.value, SessionStatus.PREPARED.value}:
            raise StateMachineError(session_id, "prepare", request_id=self._request_id())

        if session.orchestrator is None:
            self._build_orchestrator(session)

        self._acquire_lock("playback_backend", session_id)
        session.owned_locks.add("playback_backend")
        if session.mode == "live":
            self._acquire_lock("fc11_source", session_id)
            session.owned_locks.add("fc11_source")

        session.frames = make_synthetic_frames(
            session_id=session.id,
            scenario=session.parameters.get("scenario", "stable"),
            count=int(session.parameters.get("frame_count", 10)),
            timestamp_step=float(session.parameters.get("timestamp_step", 1.0)),
        )

        readiness = self._readiness(session)
        session.status = (
            SessionStatus.READY.value
            if readiness["ready"]
            else SessionStatus.PREPARED.value
        )
        session.updated_at = time.time()
        return session.response_dict()

    def _readiness(self, session: APISession) -> dict[str, Any]:
        blocking: list[str] = []
        warnings: list[str] = []
        if session.orchestrator is None:
            blocking.append("orchestrator_not_prepared")
            return {"ready": False, "blocking_reasons": blocking, "warnings": warnings}
        registry = session.orchestrator.asset_registry
        if registry is None or registry.get("speech_segment") is None:
            blocking.append("missing_aaron_asset")
        cache = session.orchestrator.cache
        if cache is None:
            blocking.append("voice_cache_unavailable")
        if session.gateway is not None and not session.gateway.source.connected:
            warnings.append("sensor_not_connected")
        if session.orchestrator.safety.force_baseline_active:
            warnings.append("baseline_forced")
        ready = not blocking
        return {"ready": ready, "blocking_reasons": blocking, "warnings": warnings}

    def get_readiness(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        report = self._readiness(session)
        if (
            report["ready"]
            and session.status == SessionStatus.PREPARED.value
        ):
            session.status = SessionStatus.READY.value
            session.updated_at = time.time()
        return report

    def _start_session(self, session: APISession) -> None:
        if session.status != SessionStatus.READY.value:
            raise StateMachineError(session.id, "start", request_id=self._request_id())
        session.status = SessionStatus.STARTING.value
        session.updated_at = time.time()
        if session.orchestrator is None:
            raise CLM05APIError(
                code="orchestrator_not_prepared",
                message="Orchestrator is not prepared",
                status_code=400,
                request_id=self._request_id(),
                resource_id=session.id,
            )
        gateway = session.gateway
        if gateway is None:
            raise CLM05APIError(
                code="gateway_not_prepared",
                message="Gateway is not prepared",
                status_code=400,
                request_id=self._request_id(),
                resource_id=session.id,
            )
        gateway.source.connect()
        session.orchestrator.start()
        session.status = SessionStatus.RUNNING.value
        session.updated_at = time.time()

    def _step_session(self, session: APISession) -> dict[str, Any]:
        if session.status != SessionStatus.RUNNING.value:
            raise StateMachineError(session.id, "step", request_id=self._request_id())
        if session.orchestrator is None:
            raise StateMachineError(session.id, "step", request_id=self._request_id())
        if session.frame_index >= len(session.frames):
            return {"done": True, "frame_index": session.frame_index}
        frame = session.frames[session.frame_index]
        receipt: LiveLoopCycleReceipt = session.orchestrator.run_step(frame)
        session.frame_index += 1
        return {"done": False, "receipt": receipt.as_dict()}

    def control_session(
        self,
        session_id: str,
        command: str,
        parameters: dict[str, Any],
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        self._check_mutations()
        payload = {
            "session_id": session_id,
            "command": command,
            "parameters": parameters,
        }

        def factory() -> dict[str, Any]:
            session = self.get_session(session_id)
            action = ControlCommand(command)
            details: dict[str, Any] = {}
            if action == ControlCommand.PREPARE:
                details = self.prepare_session(session_id)
            elif action == ControlCommand.START:
                self._start_session(session)
            elif action == ControlCommand.STEP:
                details = self._step_session(session)
            elif session.orchestrator is None:
                raise StateMachineError(session_id, command, request_id=self._request_id())
            elif action == ControlCommand.PAUSE:
                session.orchestrator.pause()
                session.status = SessionStatus.PAUSED.value
            elif action == ControlCommand.RESUME:
                session.orchestrator.resume()
                session.status = SessionStatus.RUNNING.value
            elif action == ControlCommand.STOP:
                session.orchestrator.stop()
                session.status = SessionStatus.COMPLETED.value
                self._release_owned_locks(session)
            elif action == ControlCommand.KILL:
                session.orchestrator.kill()
                session.status = SessionStatus.ABORTED.value
                self._release_owned_locks(session)
            else:
                raise StateMachineError(session_id, command, request_id=self._request_id())
            session.updated_at = time.time()
            return {"session_id": session_id, "command": command, "status": session.status, "details": details}

        return self._idempotent(idempotency_key, payload, factory)

    def delete_session(self, session_id: str) -> dict[str, Any]:
        self._check_mutations()
        session = self.get_session(session_id)
        if session.orchestrator is not None:
            try:
                session.orchestrator.stop()
            except Exception:
                pass
        self._release_owned_locks(session)
        session.close()
        if session.cache_dir is not None:
            shutil.rmtree(session.cache_dir, ignore_errors=True)
        with self._lock:
            del self.sessions[session_id]
        return {"deleted": True, "id": session_id}

    # ------------------------------------------------------------------ #
    # Sensors
    # ------------------------------------------------------------------ #

    def register_sensor(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._check_mutations()
        sensor_id = payload.get("sensor_id") or str(uuid.uuid4())
        sensor = {
            "sensor_id": sensor_id,
            "sensor_type": payload.get("sensor_type", "synthetic"),
            "connected": False,
            "session_id": None,
        }
        with self._lock:
            self.sensors[sensor_id] = sensor
        return sensor

    def list_sensors(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(s) for s in self.sensors.values()]

    def sensor_command(self, sensor_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._check_mutations()
        with self._lock:
            sensor = self.sensors.get(sensor_id)
        if not sensor:
            raise NotFoundError(sensor_id, request_id=self._request_id())
        session_id = payload.get("session_id")
        command = payload.get("command", SensorCommand.CONNECT.value)
        session: APISession | None = None
        if session_id:
            session = self.get_session(session_id)
        if command == SensorCommand.CONNECT.value:
            sensor["connected"] = True
            sensor["session_id"] = session_id
            if session is not None and session.gateway is not None:
                session.gateway.source.connect()
        elif command == SensorCommand.DISCONNECT.value:
            sensor["connected"] = False
            sensor["session_id"] = None
            if session is not None:
                if session.gateway is not None:
                    session.gateway.source.disconnect()
                if session.orchestrator is not None:
                    session.orchestrator.safety.force_baseline()
        else:
            raise CLM05APIError(
                code="invalid_sensor_command",
                message=f"Invalid sensor command: {command}",
                status_code=400,
                request_id=self._request_id(),
                resource_id=sensor_id,
            )
        return dict(sensor)

    # ------------------------------------------------------------------ #
    # Stimuli
    # ------------------------------------------------------------------ #

    def list_stimuli(self, session_id: str | None) -> list[dict[str, Any]]:
        registry: AudioAssetRegistry | None = None
        if session_id:
            session = self.get_session(session_id)
            if session.orchestrator is not None:
                registry = session.orchestrator.asset_registry
        items: list[dict[str, Any]] = []
        if registry is not None:
            for asset in registry.assets():
                items.append({
                    "stimulus_id": asset.asset_id,
                    "label": asset.label,
                    "source_text": None,
                    "tts_text": None,
                    "locale": None,
                    "duration_ms": int(asset.duration * 1000) if asset.duration else None,
                    "available": True,
                })
        if not items:
            items = [
                {"stimulus_id": "speech_segment", "label": "Giuseppe/Aaron bilingual composite", "source_text": None, "tts_text": None, "locale": "he-IL", "duration_ms": 0, "available": False},
            ]
        return items

    def get_stimulus(self, stimulus_id: str, session_id: str | None) -> dict[str, Any]:
        items = self.list_stimuli(session_id)
        for item in items:
            if item["stimulus_id"] == stimulus_id:
                return item
        raise NotFoundError(stimulus_id, request_id=self._request_id())

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #

    def list_events(
        self,
        session_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        session = self.get_session(session_id)
        if session.store is None:
            raise NotFoundError(session_id, request_id=self._request_id())
        total = session.store.get_last_sequence(SessionID(session_id))
        from_seq = max(1, (page - 1) * page_size + 1)
        to_seq = min(total, page * page_size) if total else 0
        if to_seq < from_seq:
            items: list[dict[str, Any]] = []
        else:
            events = session.store.read(SessionID(session_id), from_seq=from_seq, to_seq=to_seq)
            items = [
                {
                    "event_id": str(e.event_id),
                    "event_type": e.event_type,
                    "session_sequence_number": e.session_sequence_number,
                    "timestamp": e.timestamp,
                    "component": e.component,
                }
                for e in events
            ]
        return {
            "session_id": session_id,
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items,
        }

    def sse_event_stream(self, session_id: str, last_event_id: str | None) -> queue.Queue[dict[str, Any] | None]:
        session = self.get_session(session_id)
        q: queue.Queue[dict[str, Any] | None] = queue.Queue()
        seen = set()
        with session.sse_lock:
            for ev in session.sse_events:
                ev_id = ev.get("event_id")
                if last_event_id and ev_id and ev_id == last_event_id:
                    seen.add(ev_id)
                    continue
                if last_event_id and ev_id and ev_id in seen:
                    continue
                if ev_id:
                    seen.add(ev_id)
                q.put(ev)
        return q

    # ------------------------------------------------------------------ #
    # Exports
    # ------------------------------------------------------------------ #

    def _session_events(self, session_id: str) -> list[Event]:
        session = self.get_session(session_id)
        if session.store is None:
            return []
        return cast(list[Event], session.store.read(SessionID(session_id)))

    def export_events(self, session_id: str, fmt: str) -> tuple[str, str]:
        events = self._session_events(session_id)
        if fmt == "jsonl":
            body = _export_events_jsonl(events)
            media = "application/x-ndjson"
        else:
            body = _export_events_json(events)
            media = "application/json"
        return body, media

    def export_summary(self, session_id: str, fmt: str) -> tuple[str, str]:
        events = self._session_events(session_id)
        counts: dict[str, int] = {}
        for e in events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        session = self.get_session(session_id)
        data = {
            "session_id": session_id,
            "record_count": len(events),
            "event_type_counts": counts,
            "status": session.status,
            "redacted": True,
        }
        body = _stable_json(data) if fmt != "jsonl" else _stable_json(data) + "\n"
        media = "application/json" if fmt != "jsonl" else "application/x-ndjson"
        return body, media

    def export_manifest(self, session_id: str, fmt: str) -> tuple[str, str]:
        events = self._session_events(session_id)
        events_json = _export_events_json(events)
        summary_data = {
            "session_id": session_id,
            "record_count": len(events),
            "redacted": True,
        }
        summary_json = _stable_json(summary_data)
        manifest = {
            "session_id": session_id,
            "record_count": len(events),
            "event_export_checksum": hashlib.sha256(events_json.encode("utf-8")).hexdigest(),
            "summary_checksum": hashlib.sha256(summary_json.encode("utf-8")).hexdigest(),
            "redacted": True,
            "generated_at": time.time(),
        }
        body = _stable_json(manifest) if fmt != "jsonl" else _stable_json(manifest) + "\n"
        media = "application/json" if fmt != "jsonl" else "application/x-ndjson"
        return body, media

    def request_export(self, session_id: str, fmt: str) -> dict[str, Any]:
        self._check_mutations()
        _, media = self.export_events(session_id, fmt)
        body, _ = self.export_events(session_id, fmt)
        checksum = hashlib.sha256(body.encode("utf-8")).hexdigest()
        return {
            "session_id": session_id,
            "export_id": str(uuid.uuid4()),
            "format": fmt,
            "download_url": f"/api/v1/sessions/{session_id}/export/events?format={fmt}",
            "checksum": checksum,
            "record_count": len(self._session_events(session_id)),
            "redacted": True,
        }

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def health(self) -> dict[str, Any]:
        warnings: list[str] = []
        if self._base_store_path is None:
            warnings.append("in_memory_store")
        ready = self.accepting_mutations
        return {
            "status": "ok" if ready else "degraded",
            "ready": ready,
            "blocking_reasons": [] if ready else ["not_accepting_mutations"],
            "warnings": warnings,
            "version": self.config.api_version,
        }

    def shutdown(self) -> None:
        self.accepting_mutations = False
        for session in list(self.sessions.values()):
            if session.orchestrator is not None:
                try:
                    session.orchestrator.stop()
                except Exception:
                    pass
            self._release_owned_locks(session)
            session.close()
