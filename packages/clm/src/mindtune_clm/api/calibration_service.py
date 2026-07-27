"""Service layer for CLM-07 calibration endpoints."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, cast

from mindtune_clm.calibration.events import (
    CalibrationEventType,
    make_calibration_event,
)
from mindtune_clm.calibration.fixture_clm07 import (
    build_calibration_session as _fixture_session,
)
from mindtune_clm.calibration.health import CalibrationHealth, CalibrationReadinessEvaluator
from mindtune_clm.calibration.models import (
    CalibrationProfile,
    CalibrationReadiness,
    CalibrationSession,
    CalibrationSessionStatus,
    ProfileStatus,
)
from mindtune_clm.calibration.profiles import (
    ProfileBuilder,
    ProfileSelector,
    recalibration_recommendation,
)
from mindtune_clm.calibration.protocol import CalibrationProtocol
from mindtune_clm.calibration.repository import InMemoryCalibrationProfileRepository


def _new_id(prefix: str = "cal") -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _payload_hash(payload: Any) -> str:
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SelectionResult:
    profile_id: str | None
    profile_version: str | None
    reason: str


class CalibrationAPIService:
    """In-memory service for calibration sessions and profiles."""

    def __init__(self) -> None:
        self.sessions: dict[str, CalibrationSession] = {}
        self.repository = InMemoryCalibrationProfileRepository()
        self.protocol = CalibrationProtocol.default()
        self.selector = ProfileSelector(self.protocol)
        self.idempotency: dict[str, dict[str, Any]] = {}
        self.events: list[dict[str, Any]] = []
        self._accepting_mutations = True

    # ------------------------------------------------------------------ #
    # Idempotency
    # ------------------------------------------------------------------ #
    def _idempotent(
        self,
        key: str | None,
        payload: Any,
        factory: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        if not key:
            return factory()
        phash = _payload_hash(payload)
        record = self.idempotency.get(key)
        if record is not None:
            if record["payload_hash"] != phash:
                raise ValueError(f"idempotency conflict for key {key}")
            return cast(dict[str, Any], record["response"])
        response = factory()
        self.idempotency[key] = {
            "payload_hash": phash,
            "response": response,
            "created_at": time.time(),
        }
        return response

    def _emit(self, event_type: str, session_id: str, payload: dict[str, Any]) -> None:
        event = make_calibration_event(
            event_type=event_type,
            session_id=session_id,
            payload=payload,
            sequence=len(self.events) + 1,
        )
        self.events.append(event.as_dict())

    # ------------------------------------------------------------------ #
    # Session lifecycle
    # ------------------------------------------------------------------ #
    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        participant_id = payload["participant_id"]
        protocol_id = payload.get("protocol_id", self.protocol.protocol_id)
        protocol_version = payload.get("protocol_version", self.protocol.protocol_version)
        protocol = (
            CalibrationProtocol.by_id(protocol_id, protocol_version) or self.protocol
        )
        session_id = _new_id("cal-sess")
        session = CalibrationSession(
            session_id=session_id,
            participant_id=participant_id,
            protocol=protocol,
            sensor_family=payload.get("sensor_family", "fc11"),
            sensor_config_fingerprint=payload.get("sensor_config_fingerprint", ""),
            parser_version=payload.get("parser_version", ""),
            feature_schema_version=payload.get("feature_schema_version", ""),
            status=CalibrationSessionStatus.CREATED,
            created_at=time.time(),
            updated_at=time.time(),
        )
        self.sessions[session_id] = session
        self._emit(
            CalibrationEventType.CALIBRATION_SESSION_CREATED,
            session_id,
            {"session_id": session_id, "participant_id": participant_id},
        )
        return self._session_response(session)

    def _session_response(self, session: CalibrationSession) -> dict[str, Any]:
        return {
            "session_id": session.session_id,
            "participant_id": session.participant_id,
            "protocol_id": session.protocol.protocol_id if session.protocol else None,
            "protocol_version": session.protocol.protocol_version if session.protocol else None,
            "status": session.status.value,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "pinned_profile_id": session.pinned_profile_id,
            "pinned_profile_version": session.pinned_profile_version,
        }

    def get_session(self, session_id: str) -> CalibrationSession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"calibration session {session_id} not found")
        return session

    def list_sessions(self) -> list[dict[str, Any]]:
        return [self._session_response(s) for s in self.sessions.values()]

    def prepare(self, session_id: str) -> CalibrationReadiness:
        session = self.get_session(session_id)
        evaluator = CalibrationReadinessEvaluator(session.protocol or self.protocol)
        readiness = evaluator.evaluate(session)
        session.updated_at = time.time()
        self._emit(
            CalibrationEventType.CALIBRATION_READINESS_EVALUATED,
            session_id,
            readiness.as_dict(),
        )
        return readiness

    def start(self, session_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if session.status not in {
            CalibrationSessionStatus.CREATED,
            CalibrationSessionStatus.PREPARED,
            CalibrationSessionStatus.READINESS_CHECKED,
        }:
            raise ValueError(f"cannot start from status {session.status.value}")

        scenario = parameters.get("synthetic_scenario", "valid")
        if scenario == "valid":
            fixture = _fixture_session(
                session.participant_id,
                accepted_per_block=15,
                sensor_config_fingerprint=session.sensor_config_fingerprint,
            )
        elif scenario == "insufficient":
            fixture = _fixture_session(
                session.participant_id,
                accepted_per_block=2,
                sensor_config_fingerprint=session.sensor_config_fingerprint,
            )
        elif scenario == "unstable":
            fixture = _fixture_session(
                session.participant_id,
                accepted_per_block=15,
                noise=1.0,
                sensor_config_fingerprint=session.sensor_config_fingerprint,
            )
        elif scenario == "movement":
            fixture = _fixture_session(
                session.participant_id,
                accepted_per_block=15,
                movement_rate=0.6,
                sensor_config_fingerprint=session.sensor_config_fingerprint,
            )
        elif scenario == "zero_dispersion":
            fixture = _fixture_session(
                session.participant_id,
                accepted_per_block=15,
                zero_dispersion=True,
                sensor_config_fingerprint=session.sensor_config_fingerprint,
            )
        else:
            fixture = _fixture_session(
                session.participant_id,
                sensor_config_fingerprint=session.sensor_config_fingerprint,
            )

        session.blocks = fixture.blocks
        session.collected_observations = fixture.collected_observations
        session.quality_summary = fixture.quality_summary
        session.updated_at = time.time()
        session.status = CalibrationSessionStatus.COLLECTING
        self._emit(
            CalibrationEventType.CALIBRATION_COLLECTION_STARTED,
            session_id,
            {"block_count": len(session.blocks)},
        )
        return self._session_response(session)

    def pause(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if session.status != CalibrationSessionStatus.COLLECTING:
            raise ValueError(f"cannot pause from {session.status.value}")
        session.status = CalibrationSessionStatus.PAUSED
        session.updated_at = time.time()
        return self._session_response(session)

    def resume(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if session.status != CalibrationSessionStatus.PAUSED:
            raise ValueError(f"cannot resume from {session.status.value}")
        session.status = CalibrationSessionStatus.COLLECTING
        session.updated_at = time.time()
        return self._session_response(session)

    def stop(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if session.status not in {
            CalibrationSessionStatus.COLLECTING,
            CalibrationSessionStatus.PAUSED,
        }:
            raise ValueError(f"cannot stop from {session.status.value}")
        session.status = CalibrationSessionStatus.VALIDATING
        session.updated_at = time.time()

        builder = ProfileBuilder()
        profile = builder.build(session)
        self.repository.add(profile)
        session.status = (
            CalibrationSessionStatus.VALID
            if profile.is_valid()
            else CalibrationSessionStatus.INSUFFICIENT_DATA
            if profile.validity_status == ProfileStatus.INSUFFICIENT_DATA
            else CalibrationSessionStatus.UNSTABLE
        )
        self._emit(
            CalibrationEventType.CALIBRATION_PROFILE_CREATED,
            session_id,
            profile.as_dict(),
        )
        return {
            "session_id": session_id,
            "status": session.status.value,
            "profile_id": profile.profile_id,
            "profile_version": profile.profile_version,
            "validity_status": profile.validity_status.value,
        }

    def abort(self, session_id: str, reason: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        session.status = CalibrationSessionStatus.ABORTED
        session.abort_reason = reason
        session.updated_at = time.time()
        self._emit(
            CalibrationEventType.CALIBRATION_SESSION_ABORTED,
            session_id,
            {"reason": reason},
        )
        return self._session_response(session)

    def readiness(self, session_id: str) -> CalibrationReadiness:
        session = self.get_session(session_id)
        if session.status == CalibrationSessionStatus.CREATED:
            evaluator = CalibrationReadinessEvaluator(session.protocol or self.protocol)
            evaluator.evaluate(session)
            session.updated_at = time.time()
        return session.readiness

    def health(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        return CalibrationHealth(
            status=session.status.value,
            ready=session.readiness.ready,
            blockers=list(session.readiness.blocking_reasons),
            warnings=list(session.readiness.warnings),
        ).as_dict()

    def summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        accepted = session.quality_summary.accepted_count
        rejected = session.quality_summary.rejected_count
        missing = session.quality_summary.missing_count
        return {
            "session_id": session_id,
            "status": session.status.value,
            "block_count": len(session.blocks),
            "accepted": accepted,
            "rejected": rejected,
            "missing": missing,
        }

    # ------------------------------------------------------------------ #
    # Profiles
    # ------------------------------------------------------------------ #
    def _profile_response(self, profile: CalibrationProfile) -> dict[str, Any]:
        return {
            "profile_id": profile.profile_id,
            "profile_version": profile.profile_version,
            "participant_id": profile.participant_id,
            "sensor_family": profile.sensor_family,
            "sensor_config_fingerprint": profile.sensor_config_fingerprint,
            "feature_schema_version": profile.feature_schema_version,
            "validity_status": profile.validity_status.value,
            "accepted_observation_count": profile.accepted_observation_count,
            "rejected_observation_count": profile.rejected_observation_count,
            "created_at": profile.end_semantic_time,
            "feature_baselines": {k: v.as_dict() for k, v in profile.feature_baselines.items()},
        }

    def list_profiles(self, participant_id: str) -> list[dict[str, Any]]:
        return [self._profile_response(p) for p in self.repository.list_for_participant(participant_id)]

    def get_profile(self, participant_id: str, profile_id: str) -> dict[str, Any]:
        profile = self.repository.get(profile_id)
        if profile is None or profile.participant_id != participant_id:
            raise KeyError("profile not found")
        return self._profile_response(profile)

    def validate_profile(self, participant_id: str, profile_id: str) -> dict[str, Any]:
        profile = self.repository.get(profile_id)
        if profile is None or profile.participant_id != participant_id:
            raise KeyError("profile not found")
        from dataclasses import replace
        new_profile = replace(profile, validity_status=ProfileStatus.VALID)
        self.repository.add(new_profile)
        self._emit(
            CalibrationEventType.CALIBRATION_PROFILE_VALIDATED,
            profile_id,
            {"profile_id": profile_id, "profile_version": new_profile.profile_version},
        )
        return self._profile_response(new_profile)

    def invalidate_profile(self, participant_id: str, profile_id: str, reason: str) -> dict[str, Any]:
        if not reason:
            raise ValueError("invalidation requires a reason")
        profile = self.repository.invalidate(profile_id, reason)
        if profile is None:
            raise KeyError("profile not found")
        self._emit(
            CalibrationEventType.CALIBRATION_PROFILE_INVALIDATED,
            profile_id,
            {"profile_id": profile_id, "reason": reason},
        )
        return self._profile_response(profile)

    def select_profile(
        self,
        participant_id: str,
        profile_id: str | None = None,
        sensor_family: str = "fc11",
        sensor_config_fingerprint: str = "fc11.default",
        parser_version: str = "fc11.parser.v1",
        feature_schema_version: str = "clm07.schema.v1",
    ) -> SelectionResult:
        profiles = self.repository.list_for_participant(participant_id)
        result = self.selector.select(
            profiles,
            participant_id,
            sensor_family,
            sensor_config_fingerprint,
            parser_version,
            feature_schema_version,
            pinned_profile_id=profile_id,
        )
        self._emit(
            CalibrationEventType.CALIBRATION_PROFILE_SELECTED,
            participant_id,
            result.as_dict(),
        )
        return SelectionResult(
            profile_id=result.profile_id,
            profile_version=result.profile_version,
            reason=result.reason,
        )

    def select_profile_for_session(
        self,
        participant_id: str,
        sensor_family: str = "fc11",
        sensor_config_fingerprint: str = "fc11.default",
        parser_version: str = "fc11.parser.v1",
        feature_schema_version: str = "clm07.schema.v1",
        pinned_profile_id: str | None = None,
    ) -> tuple[str | None, str | None]:
        result = self.select_profile(
            participant_id,
            pinned_profile_id,
            sensor_family,
            sensor_config_fingerprint,
            parser_version,
            feature_schema_version,
        )
        return result.profile_id, result.profile_version

    def calibration_status(self, participant_id: str) -> dict[str, Any]:
        profiles = self.repository.list_for_participant(participant_id)
        valid = [p for p in profiles if p.is_valid()]
        return {
            "participant_id": participant_id,
            "total_profiles": len(profiles),
            "valid_profiles": len(valid),
            "latest_profile_id": valid[-1].profile_id if valid else None,
        }

    def export_profile(
        self,
        participant_id: str,
        profile_id: str | None,
        fmt: str = "json",
    ) -> dict[str, Any]:
        profile: CalibrationProfile | None
        if profile_id is None:
            profiles = self.repository.list_for_participant(participant_id)
            if not profiles:
                raise KeyError("no profiles")
            profile = profiles[-1]
        else:
            profile = self.repository.get(profile_id)
        if profile is None or profile.participant_id != participant_id:
            raise KeyError("profile not found")
        payload = profile.as_dict()
        checksum = hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()
        return {
            "export_id": _new_id("export"),
            "profile_id": profile.profile_id,
            "format": fmt,
            "checksum": checksum,
            "record_count": len(profile.feature_baselines) + 1,
            "redacted": True,
            "payload": payload,
        }

    def all_events(self) -> list[dict[str, Any]]:
        return list(self.events)

    def drift_recommendation(
        self,
        participant_id: str,
        sessions_since_calibration: int,
        drift_sessions: int,
    ) -> str | None:
        profiles = self.repository.list_for_participant(participant_id)
        current = profiles[-1] if profiles else None
        return recalibration_recommendation(
            current,
            [],
            sessions_since_calibration,
            drift_sessions,
        )
