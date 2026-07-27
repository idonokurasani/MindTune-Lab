import * as React from 'react';
import { StatusBadge } from './StatusBadge';
import type { HealthResponse } from '../api/models';

interface HealthPanelProps {
  health: HealthResponse | null;
}

export const HealthPanel: React.FC<HealthPanelProps> = ({ health }) => {
  const ready = health?.ready ?? false;
  const status: 'healthy' | 'degraded' | 'failed' =
    health?.status === 'ok' ? 'healthy' : health?.status === 'degraded' ? 'degraded' : 'failed';
  const items = [
    { key: 'api', label: 'API', status: status },
    { key: 'live-loop', label: 'Live Loop', status: ready ? 'healthy' : 'degraded' },
    { key: 'voice-cache', label: 'Voice Cache', status: ready ? 'healthy' : 'stopped' },
    { key: 'renderer', label: 'Renderer', status: ready ? 'healthy' : 'stopped' },
    { key: 'playback', label: 'Playback', status: ready ? 'healthy' : 'disconnected' },
    { key: 'event-store', label: 'Event Store', status: ready ? 'healthy' : 'stopped' },
    { key: 'mpe', label: 'MPE', status: ready ? 'healthy' : 'disconnected' },
    { key: 'sensor', label: 'Sensor', status: ready ? 'healthy' : 'disconnected' },
  ] as const;

  return (
    <section className="card" aria-label="Health panel">
      <h2>System Health</h2>
      <div className="grid">
        {items.map((i) => (
          <StatusBadge key={i.key} status={i.status} label={i.label} />
        ))}
      </div>
      {health?.warnings && health.warnings.length > 0 && (
        <ul className="list" aria-label="Health warnings">
          {health.warnings.map((w, idx) => (
            <li key={idx}>{w}</li>
          ))}
        </ul>
      )}
    </section>
  );
};
