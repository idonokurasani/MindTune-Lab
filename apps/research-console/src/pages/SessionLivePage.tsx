import * as React from 'react';
import { useEffect, useState } from 'react';
import { AudioPanel } from '../components/AudioPanel';
import { DecisionPanel } from '../components/DecisionPanel';
import { EventTimeline } from '../components/EventTimeline';
import { OutcomePanel } from '../components/OutcomePanel';
import { ReadinessPanel } from '../components/ReadinessPanel';
import { SafetyControls } from '../components/SafetyControls';
import { SensorPanel } from '../components/SensorPanel';
import { StatusBadge } from '../components/StatusBadge';
import { api } from '../api/client';
import { useReadiness } from '../hooks/useReadiness';
import { useSession } from '../hooks/useSession';
import { useSessionEvents } from '../hooks/useSessionEvents';
import type { ControlCommandName, SensorResponse, StimulusResponse } from '../api/models';

interface SessionLivePageProps {
  sessionId: string | null;
}

export const SessionLivePage: React.FC<SessionLivePageProps> = ({ sessionId }) => {
  const { session, loadSession, sendControl, loading } = useSession();
  const { readiness } = useReadiness(sessionId ?? null, 1500);
  const sse = useSessionEvents(sessionId ?? null, 500);
  const [sensor, setSensor] = useState<SensorResponse | null>(null);
  const [stimuli, setStimuli] = useState<StimulusResponse[]>([]);

  useEffect(() => {
    if (!sessionId) return;
    loadSession(sessionId);
    api.listSensors().then((r) => setSensor(r.items[0] ?? null));
    api.listStimuli(sessionId).then((r) => setStimuli(r.items));
  }, [sessionId, loadSession]);

  const handleCommand = async (command: ControlCommandName) => {
    if (!sessionId) return;
    await sendControl(sessionId, { command });
    await loadSession(sessionId);
  };

  if (!sessionId) {
    return <p>Select a session first.</p>;
  }

  return (
    <section aria-label="Live session">
      <h2>Live Session</h2>
      {loading && <p>Loading session…</p>}
      {session && (
        <>
          <p>
            <strong>{session.id}</strong> — mode {session.mode} — status{' '}
            <StatusBadge status={session.status as 'healthy' | 'failed'} label={session.status} />
          </p>
          <ReadinessPanel readiness={readiness} />
          <SafetyControls onCommand={handleCommand} disabled={!session} />
          <SensorPanel
            sensor={sensor}
            onConnect={() => sensor && api.connectSensor(sensor.sensor_id, sessionId)}
            onDisconnect={() => sensor && api.disconnectSensor(sensor.sensor_id, sessionId)}
          />
          <AudioPanel stimuli={stimuli} />
          <DecisionPanel requestedState={session.status} appliedState={readiness?.ready ? 'applied' : 'pending'} />
          <OutcomePanel outcome={{ status: session.status, level: 0, tempo_ratio: 1, pause_duration_ms: 0 }} />
          <EventTimeline events={sse.events} />
        </>
      )}
    </section>
  );
};
