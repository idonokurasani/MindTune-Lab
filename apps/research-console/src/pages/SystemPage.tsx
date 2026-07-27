import * as React from 'react';
import { StatusBadge } from '../components/StatusBadge';
import type { HealthResponse, ProtocolReference, SensorResponse } from '../api/models';

interface SystemPageProps {
  health: HealthResponse | null;
  protocols: ProtocolReference[];
  sensors: SensorResponse[];
}

export const SystemPage: React.FC<SystemPageProps> = ({ health, protocols, sensors }) => {
  return (
    <section aria-label="System">
      <h2>System</h2>
      <div className="card">
        <h3>API Health</h3>
        <StatusBadge status={health?.status === 'ok' ? 'healthy' : 'degraded'} label={health?.status ?? 'unknown'} />
        <p>Version {health?.version}</p>
      </div>
      <div className="card">
        <h3>Protocols</h3>
        <ul className="list">
          {protocols.map((p) => (
            <li key={p.protocol_version_id}>
              {p.name} — <code>{p.protocol_version_id}</code>
            </li>
          ))}
        </ul>
      </div>
      <div className="card">
        <h3>Sensors</h3>
        <ul className="list">
          {sensors.map((s) => (
            <li key={s.sensor_id}>
              {s.sensor_id} ({s.sensor_type}) —{' '}
              <StatusBadge status={s.connected ? 'healthy' : 'disconnected'} label={s.connected ? 'connected' : 'disconnected'} />
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
};
