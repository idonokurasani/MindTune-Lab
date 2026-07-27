import * as React from 'react';
import { useState, useEffect } from 'react';
import { ReadinessPanel } from '../components/ReadinessPanel';
import { useReadiness } from '../hooks/useReadiness';
import { sanitizeNotes } from '../api/client';
import type { ExperimentResponse, ProtocolReference, RuntimeMode, SessionResponse } from '../api/models';

interface SessionCreatePageProps {
  experiments: ExperimentResponse[];
  protocols: ProtocolReference[];
  onCreate: (payload: {
    experiment_id?: string;
    learner_id: string;
    mode: RuntimeMode;
    protocol_version_id?: string;
    sensor_source: string;
    stimulus_set: string;
    playback_backend: string;
    notes: string;
  }) => Promise<SessionResponse>;
  onStart: (sessionId: string) => void;
}

export const SessionCreatePage: React.FC<SessionCreatePageProps> = ({
  experiments,
  protocols,
  onCreate,
  onStart,
}) => {
  const [experimentId, setExperimentId] = useState('');
  const [protocol, setProtocol] = useState(protocols[0]?.protocol_version_id ?? '');
  const [mode, setMode] = useState<RuntimeMode>('synthetic_live');
  const [learnerId, setLearnerId] = useState('anonymous');
  const [sensorSource, setSensorSource] = useState('synthetic');
  const [stimulusSet, setStimulusSet] = useState('default');
  const [playbackBackend, setPlaybackBackend] = useState('deterministic');
  const [notes, setNotes] = useState('');
  const [created, setCreated] = useState<SessionResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const { readiness } = useReadiness(created?.id ?? null);

  useEffect(() => {
    if (protocols[0]) setProtocol(protocols[0].protocol_version_id);
  }, [protocols]);

  const handleCreate = async () => {
    setBusy(true);
    try {
      const session = await onCreate({
        experiment_id: experimentId || undefined,
        learner_id: sanitizeNotes(learnerId),
        mode,
        protocol_version_id: protocol,
        sensor_source: sensorSource,
        stimulus_set: stimulusSet,
        playback_backend: playbackBackend,
        notes: sanitizeNotes(notes),
      });
      setCreated(session);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section aria-label="Create session">
      <h2>Create Session</h2>
      <div className="card">
        <div className="form-group">
          <label htmlFor="sess-experiment">Experiment</label>
          <select id="sess-experiment" value={experimentId} onChange={(e) => setExperimentId(e.target.value)}>
            <option value="">None</option>
            {experiments.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="sess-protocol">Protocol version</label>
          <select id="sess-protocol" value={protocol} onChange={(e) => setProtocol(e.target.value)}>
            {protocols.map((p) => (
              <option key={p.protocol_version_id} value={p.protocol_version_id}>
                {p.name} ({p.protocol_version_id})
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="sess-mode">Runtime mode</label>
          <select id="sess-mode" value={mode} onChange={(e) => setMode(e.target.value as RuntimeMode)}>
            <option value="replay">Replay</option>
            <option value="synthetic_live">Synthetic Live</option>
            <option value="fc11_live">FC11 Live</option>
            <option value="dry_run">Dry Run</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="sess-learner">Participant pseudonym</label>
          <input id="sess-learner" value={learnerId} onChange={(e) => setLearnerId(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="sess-sensor">Sensor source</label>
          <input id="sess-sensor" value={sensorSource} onChange={(e) => setSensorSource(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="sess-stimulus">Stimulus set</label>
          <input id="sess-stimulus" value={stimulusSet} onChange={(e) => setStimulusSet(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="sess-playback">Playback backend</label>
          <input id="sess-playback" value={playbackBackend} onChange={(e) => setPlaybackBackend(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="sess-notes">Notes</label>
          <textarea id="sess-notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <button onClick={handleCreate} disabled={busy}>
          Create Session
        </button>
        {created && (
          <div className="card">
            <p>Session {created.id} created. Status: {created.status}</p>
            <ReadinessPanel readiness={readiness} />
            <button
              onClick={() => onStart(created.id)}
              disabled={!readiness?.ready}
              aria-describedby="start-blocker"
            >
              Start Session
            </button>
            <p id="start-blocker">
              {readiness?.blocking_reasons.map((b) => `Blocker: ${b}`).join('; ')}
            </p>
          </div>
        )}
      </div>
    </section>
  );
};
