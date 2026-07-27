"""CLM-05 experimental API and control plane tests."""

from __future__ import annotations

import json
import unittest
from uuid import uuid4

from mindtune_clm.api.fixture_clm05 import auth_headers, make_test_client


class TestCLM05API(unittest.TestCase):
    """Comprehensive API tests proving session lifecycle, security, SSE, and exports."""

    def setUp(self) -> None:
        self.client = make_test_client()
        self.headers = auth_headers()

    def tearDown(self) -> None:
        self.client.close()

    def _create_session(self, mode: str = "synthetic", params: dict | None = None) -> dict:
        payload = {"mode": mode, "parameters": params or {}}
        r = self.client.post("/api/v1/sessions", json=payload, headers=self.headers)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def _control(self, session_id: str, command: str, params: dict | None = None, key: str | None = None) -> dict:
        payload = {"command": command, "parameters": params or {}}
        if key:
            payload["idempotency_key"] = key
        r = self.client.post(f"/api/v1/sessions/{session_id}/control", json=payload, headers=self.headers)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    # ------------------------------------------------------------------ #
    # Health / protocols / experiments (12 properties)
    # ------------------------------------------------------------------ #

    def test_health_returns_status_and_ready(self) -> None:
        r = self.client.get("/api/v1/health", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("ready", body)
        self.assertIn("blocking_reasons", body)
        self.assertIn("warnings", body)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["version"], "v1")

    def test_health_live(self) -> None:
        r = self.client.get("/api/v1/health/live")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_protocols_list_and_lookup(self) -> None:
        r = self.client.get("/api/v1/protocols")
        self.assertEqual(r.status_code, 200)
        ids = [p["protocol_version_id"] for p in r.json()["items"]]
        self.assertIn("clm-05-experimental.v1", ids)
        get = self.client.get("/api/v1/protocols/clm-05-experimental.v1")
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.json()["protocol_version_id"], "clm-05-experimental.v1")

    def test_experiments_crud(self) -> None:
        create = self.client.post("/api/v1/experiments", json={"name": "exp-a"}, headers=self.headers)
        self.assertEqual(create.status_code, 201)
        exp_id = create.json()["id"]
        self.assertEqual(create.json()["name"], "exp-a")
        get = self.client.get(f"/api/v1/experiments/{exp_id}")
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.json()["id"], exp_id)
        list_r = self.client.get("/api/v1/experiments")
        self.assertEqual(list_r.status_code, 200)
        self.assertIn(exp_id, [e["id"] for e in list_r.json()["items"]])
        delete = self.client.delete(f"/api/v1/experiments/{exp_id}", headers=self.headers)
        self.assertEqual(delete.status_code, 200)
        self.assertTrue(delete.json()["deleted"])

    # ------------------------------------------------------------------ #
    # Session lifecycle state machine (12 properties)
    # ------------------------------------------------------------------ #

    def test_session_create_and_get(self) -> None:
        s = self._create_session()
        self.assertIn("id", s)
        self.assertEqual(s["status"], "created")
        get = self.client.get(f"/api/v1/sessions/{s['id']}", headers=self.headers)
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.json()["id"], s["id"])
        self.assertEqual(get.json()["mode"], "synthetic")

    def test_session_state_machine(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self.assertEqual(s["status"], "created")
        p = self._control(sid, "prepare")
        self.assertIn(p["status"], {"prepared", "ready"})
        ready = self.client.get(f"/api/v1/sessions/{sid}/readiness", headers=self.headers)
        self.assertEqual(ready.status_code, 200)
        if ready.json()["ready"]:
            self.assertEqual(p["status"], "ready")
            start = self._control(sid, "start")
            self.assertEqual(start["status"], "running")
            step = self._control(sid, "step")
            self.assertIn("receipt", step["details"])
            pause = self._control(sid, "pause")
            self.assertEqual(pause["status"], "paused")
            resume = self._control(sid, "resume")
            self.assertEqual(resume["status"], "running")
            stop = self._control(sid, "stop")
            self.assertEqual(stop["status"], "completed")

    def test_session_delete(self) -> None:
        s = self._create_session()
        sid = s["id"]
        r = self.client.delete(f"/api/v1/sessions/{sid}", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["deleted"])
        get = self.client.get(f"/api/v1/sessions/{sid}", headers=self.headers)
        self.assertEqual(get.status_code, 404)

    # ------------------------------------------------------------------ #
    # Synthetic scenarios A-G (24 properties)
    # ------------------------------------------------------------------ #

    def test_a_step_is_deterministic_across_idempotent_calls(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self._control(sid, "prepare")
        self._control(sid, "start")
        key = str(uuid4())
        step1 = self._control(sid, "step", key=key)
        step2 = self._control(sid, "step", key=key)
        self.assertEqual(step1["details"]["receipt"]["outcome_id"], step2["details"]["receipt"]["outcome_id"])
        self.assertEqual(step1["details"]["receipt"]["cognitive_state"], step2["details"]["receipt"]["cognitive_state"])

    def test_b_synthetic_live_reaches_intervention_outcome(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self._control(sid, "prepare")
        self._control(sid, "start")
        self._control(sid, "step")
        events = self.client.get(f"/api/v1/sessions/{sid}/events", headers=self.headers).json()["items"]
        types = [e["event_type"] for e in events]
        self.assertIn("session_created", types)
        self.assertIn("session_started", types)
        self.assertIn("live_closed_loop_started", types)
        self.assertIn("live_closed_loop_intervention_outcome", types)

    def test_c_readiness_fails_without_aaron_asset(self) -> None:
        s = self._create_session(params={"skip_voice_cache": True})
        sid = s["id"]
        p = self._control(sid, "prepare")
        self.assertEqual(p["status"], "prepared")
        r = self.client.get(f"/api/v1/sessions/{sid}/readiness", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["ready"])
        self.assertIn("missing_aaron_asset", body["blocking_reasons"])

    def test_d_sensor_disconnect_forces_baseline(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self._control(sid, "prepare")
        sensor = self.client.post("/api/v1/sensors", json={"sensor_id": "s1", "sensor_type": "synthetic"}, headers=self.headers)
        self.assertEqual(sensor.status_code, 201)
        self.client.post("/api/v1/sensors/s1/connect", json={"session_id": sid}, headers=self.headers)
        disc = self.client.post("/api/v1/sensors/s1/disconnect", json={"session_id": sid}, headers=self.headers)
        self.assertEqual(disc.status_code, 200)
        r = self.client.get(f"/api/v1/sessions/{sid}/readiness", headers=self.headers)
        self.assertIn("baseline_forced", r.json()["warnings"])

    def test_e_kill_through_api(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self._control(sid, "prepare")
        self._control(sid, "start")
        self._control(sid, "step")
        kill = self.client.post(f"/api/v1/sessions/{sid}/control", json={"command": "kill"}, headers=self.headers)
        self.assertEqual(kill.status_code, 200)
        self.assertEqual(kill.json()["status"], "aborted")
        get = self.client.get(f"/api/v1/sessions/{sid}", headers=self.headers)
        self.assertEqual(get.json()["status"], "aborted")

    def test_f_idempotency_same_key_same_result_and_conflict(self) -> None:
        key = str(uuid4())
        payload = {"mode": "synthetic", "learner_id": "anon", "idempotency_key": key}
        r1 = self.client.post("/api/v1/sessions", json=payload, headers=self.headers)
        self.assertEqual(r1.status_code, 201)
        r2 = self.client.post("/api/v1/sessions", json=payload, headers=self.headers)
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        payload2 = {"mode": "synthetic", "learner_id": "other", "idempotency_key": key}
        r3 = self.client.post("/api/v1/sessions", json=payload2, headers=self.headers)
        self.assertEqual(r3.status_code, 422)
        self.assertEqual(r3.json()["code"], "idempotency_conflict")

    def test_g_sse_reconnect_skips_prior_events(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self._control(sid, "prepare")
        self._control(sid, "start")
        self._control(sid, "step")
        events = self.client.get(f"/api/v1/sessions/{sid}/events", headers=self.headers).json()["items"]
        self.assertTrue(len(events) >= 2)
        last_id = events[0]["event_id"]
        with self.client.stream("GET", f"/api/v1/sessions/{sid}/events/stream?last_event_id={last_id}", headers=self.headers) as response:
            text = response.read().decode("utf-8")
        data_lines = [line for line in text.split("\n") if line.startswith("data: ")]
        ids = [json.loads(line[6:])["event_id"] for line in data_lines]
        self.assertNotIn(last_id, ids)
        self.assertTrue(any("heartbeat" in line or line.startswith(":heartbeat") for line in text.split("\n")))

    # ------------------------------------------------------------------ #
    # Sensors and stimuli (10 properties)
    # ------------------------------------------------------------------ #

    def test_sensors_register_connect_disconnect(self) -> None:
        r = self.client.post("/api/v1/sensors", json={"sensor_id": "sx", "sensor_type": "synthetic"}, headers=self.headers)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["sensor_id"], "sx")
        list_r = self.client.get("/api/v1/sensors", headers=self.headers)
        self.assertIn("sx", [s["sensor_id"] for s in list_r.json()["items"]])
        get = self.client.get("/api/v1/sensors/sx", headers=self.headers)
        self.assertEqual(get.status_code, 200)
        self.client.post("/api/v1/sensors/sx/connect", json={}, headers=self.headers)
        get2 = self.client.get("/api/v1/sensors/sx", headers=self.headers)
        self.assertTrue(get2.json()["connected"])
        self.client.post("/api/v1/sensors/sx/disconnect", json={}, headers=self.headers)
        get3 = self.client.get("/api/v1/sensors/sx", headers=self.headers)
        self.assertFalse(get3.json()["connected"])

    def test_stimuli_list_after_prepare(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self._control(sid, "prepare")
        r = self.client.get(f"/api/v1/stimuli?session_id={sid}", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        items = r.json()["items"]
        self.assertTrue(len(items) > 0)
        self.assertIn("speech_segment", [i["stimulus_id"] for i in items])
        get = self.client.get(f"/api/v1/stimuli/speech_segment?session_id={sid}", headers=self.headers)
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.json()["stimulus_id"], "speech_segment")

    # ------------------------------------------------------------------ #
    # Events pagination (6 properties)
    # ------------------------------------------------------------------ #

    def test_events_pagination(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self._control(sid, "prepare")
        self._control(sid, "start")
        self._control(sid, "step")
        r = self.client.get(f"/api/v1/sessions/{sid}/events?page_size=5", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["session_id"], sid)
        self.assertEqual(body["page_size"], 5)
        self.assertIn("items", body)
        self.assertIn("total", body)

    # ------------------------------------------------------------------ #
    # Exports and privacy (12 properties)
    # ------------------------------------------------------------------ #

    def test_export_events_redacts_participant_identity(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self._control(sid, "prepare")
        self._control(sid, "start")
        self._control(sid, "step")
        r = self.client.get(f"/api/v1/sessions/{sid}/export/events?format=json", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        events = r.json()
        payload = json.dumps(events)
        self.assertNotIn("learner_id", payload)
        self.assertIn("[REDACTED]", payload)

    def test_export_summary_and_manifest(self) -> None:
        s = self._create_session()
        sid = s["id"]
        self._control(sid, "prepare")
        self._control(sid, "start")
        self._control(sid, "step")
        summary = self.client.get(f"/api/v1/sessions/{sid}/export/summary?format=json", headers=self.headers)
        self.assertEqual(summary.status_code, 200)
        self.assertIn("record_count", summary.json())
        self.assertIn("event_type_counts", summary.json())
        manifest = self.client.get(f"/api/v1/sessions/{sid}/export/manifest?format=json", headers=self.headers)
        self.assertEqual(manifest.status_code, 200)
        body = manifest.json()
        self.assertIn("event_export_checksum", body)
        self.assertIn("summary_checksum", body)
        self.assertTrue(body["redacted"])
        req = self.client.post(f"/api/v1/sessions/{sid}/exports", json={"format": "json"}, headers=self.headers)
        self.assertEqual(req.status_code, 200)
        self.assertIn("download_url", req.json())

    # ------------------------------------------------------------------ #
    # Security (8 properties)
    # ------------------------------------------------------------------ #

    def test_mutations_require_token(self) -> None:
        # Default test client enforces token (non-loopback client).
        s = self._create_session()
        sid = s["id"]
        no_token = self.client.post(f"/api/v1/sessions/{sid}/control", json={"command": "prepare"})
        self.assertEqual(no_token.status_code, 401)
        bad_token = self.client.post(f"/api/v1/sessions/{sid}/control", json={"command": "prepare"}, headers={"Authorization": "Bearer wrong"})
        self.assertEqual(bad_token.status_code, 401)
        good = self.client.post(f"/api/v1/sessions/{sid}/control", json={"command": "prepare"}, headers=self.headers)
        self.assertEqual(good.status_code, 200)

    def test_request_size_limit(self) -> None:
        big = {"mode": "synthetic", "parameters": {"x": "a" * 2_000_000}}
        r = self.client.post("/api/v1/sessions", json=big, headers=self.headers)
        self.assertEqual(r.status_code, 413)

    def test_cors_no_wildcard(self) -> None:
        r = self.client.options("/api/v1/health", headers={"Origin": "http://localhost:8005", "Access-Control-Request-Method": "GET"})
        self.assertEqual(r.status_code, 200)
        header = r.headers.get("access-control-allow-origin")
        self.assertNotEqual(header, "*")


if __name__ == "__main__":
    unittest.main()
