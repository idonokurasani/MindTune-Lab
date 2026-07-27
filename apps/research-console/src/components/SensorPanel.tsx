import * as React from 'react';
import { StatusBadge } from './StatusBadge';
import type { SensorResponse } from '../api/models';

interface SensorPanelProps {
  sensor: SensorResponse | null;
  onConnect: () => void;
  onDisconnect: () => void;
}

export const SensorPanel: React.FC<SensorPanelProps> = ({ sensor, onConnect, onDisconnect }) => {
  if (!sensor) {
    return (
      <section className="card" aria-label="Sensor panel">
        <h2>Sensor</h2>
        <p>No sensor registered.</p>
      </section>
    );
  }
  return (
    <section className="card" aria-label="Sensor panel">
      <h2>Sensor</h2>
      <p>
        <StatusBadge status={sensor.connected ? 'healthy' : 'disconnected'} label={sensor.sensor_id} />
      </p>
      <p>Type: {sensor.sensor_type}</p>
      <div className="grid">
        <button onClick={onConnect}>Connect</button>
        <button onClick={onDisconnect}>Disconnect</button>
      </div>
    </section>
  );
};
