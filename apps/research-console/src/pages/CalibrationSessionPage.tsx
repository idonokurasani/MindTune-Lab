import * as React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { ReadinessPanel } from '../components/ReadinessPanel';
import { StatusBadge } from '../components/StatusBadge';
import type {
  CalibrationReadinessResponse,
  CalibrationSession,
  CalibrationSessionResponse,
  CalibrationSummaryResponse,
} from '../api/models';

type CalibrationCommand = 'prepare' | 'start' | 'pause' | 'resume' | 'stop' | 'abort';

const CalibrationSessionPage: React.FC = () => {
  const [participantId, setParticipantId] = useState('anon-1');
  const [scenario, setScenario] = useState('valid');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [session, setSession] = useState<CalibrationSession | null>(null);
  const [readiness, setReadiness] = useState<CalibrationReadinessResponse | null>(null);
  const [summary, setSummary] = useState<CalibrationSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  const refresh = async (id: string) => {
    try {
      const [s, r, h] = await Promise.all([
        api.getCalibration(id),
        api.getCalibrationReadiness(id),
        api.getCalibrationSummary(id),
      ]);
      setSession(s);
      setReadiness(r);
      setSummary(h);
    } catch {
      setError('Failed to refresh calibration session');
    }
  };

  useEffect(() => {
    if (!sessionId) return;
    refresh(sessionId);
    const interval = setInterval(() => refresh(sessionId), 1500);
    return () => clearInterval(interval);
  }, [sessionId]);

  const createSession = async () => {
    setError(null);
    try {
      const created: CalibrationSessionResponse = await api.createCalibration({
        participant_id: participantId,
        sensor_family: 'fc11',
        sensor_config_fingerprint: 'fc11.default',
        parser_version: 'fc11.parser.v1',
        feature_schema_version: 'clm07.schema.v1',
      });
      setSessionId(created.session_id);
      setSession(created);
    } catch {
      setError('Failed to create calibration session');
    }
  };

  const sendCommand = async (command: CalibrationCommand) => {
    if (!sessionId) return;
    setError(null);
    try {
      switch (command) {
        case 'prepare':
          await api.prepareCalibration(sessionId);
          break;
        case 'start':
          await api.startCalibration(sessionId, { synthetic_scenario: scenario });
          break;
        case 'pause':
          await api.pauseCalibration(sessionId);
          break;
        case 'resume':
          await api.resumeCalibration(sessionId);
          break;
        case 'stop':
          await api.stopCalibration(sessionId);
          break;
        case 'abort':
          await api.abortCalibration(sessionId);
          break;
      }
      await refresh(sessionId);
    } catch {
      setError(`Failed to ${command} calibration session`);
    }
  };

  const elapsedSeconds =
    session && session.created_at > 0
      ? Math.max(0, Math.floor((now / 1000 - session.created_at)))
      : 0;

  return (
    <section aria-label="Calibration session">
      <h2>Calibration Session</h2>

      <section className="card">
        <label>
          Participant pseudonym
          <input
            type="text"
            value={participantId}
            onChange={(e) => setParticipantId(e.target.value)}
            aria-label="Participant pseudonym"
          />
        </label>
        <label>
          Scenario
          <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
            <option value="valid">valid</option>
            <option value="insufficient">insufficient</option>
            <option value="unstable">unstable</option>
            <option value="movement">movement</option>
            <option value="zero_dispersion">zero_dispersion</option>
          </select>
        </label>
        <button onClick={createSession} disabled={!!sessionId}>
          Create Session
        </button>
      </section>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {session && (
        <section className="card" aria-label="Session state">
          <h3>Session {session.session_id}</h3>
          <p>
            Status: <StatusBadge status={session.status} label={session.status} />
          </p>
          <p>Elapsed: {elapsedSeconds}s</p>
          <p>Protocol: {session.protocol_id ?? '—'}</p>
          <p>Pinned profile: {session.pinned_profile_id ?? '—'}</p>
        </section>
      )}

      {session && (
        <section className="card" aria-label="Session controls">
          <button onClick={() => sendCommand('prepare')}>Prepare</button>
          <button onClick={() => sendCommand('start')}>Start</button>
          <button onClick={() => sendCommand('pause')}>Pause</button>
          <button onClick={() => sendCommand('resume')}>Resume</button>
          <button onClick={() => sendCommand('stop')}>Stop</button>
          <button onClick={() => sendCommand('abort')}>Abort</button>
        </section>
      )}

      {readiness && (
        <ReadinessPanel readiness={readiness} />
      )}

      {summary && (
        <section className="card" aria-label="Collection summary">
          <h3>Collection Summary</h3>
          <p>Blocks: {summary.block_count}</p>
          <p>Accepted windows: {summary.accepted}</p>
          <p>Rejected windows: {summary.rejected}</p>
          <p>Missing windows: {summary.missing}</p>
        </section>
      )}
    </section>
  );
};

export default CalibrationSessionPage;
