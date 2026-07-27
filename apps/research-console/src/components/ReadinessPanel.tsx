import * as React from 'react';
import { StatusBadge } from './StatusBadge';
import type { ReadinessResponse } from '../api/models';

interface ReadinessPanelProps {
  readiness: ReadinessResponse | null;
}

export const ReadinessPanel: React.FC<ReadinessPanelProps> = ({ readiness }) => {
  const ready = readiness?.ready ?? false;
  const blockers = readiness?.blocking_reasons ?? [];
  const warnings = readiness?.warnings ?? [];
  return (
    <section className="card" aria-label="Readiness panel">
      <h2>Readiness</h2>
      <StatusBadge status={ready ? 'healthy' : 'failed'} label={ready ? 'Ready' : 'Not Ready'} />
      {blockers.length > 0 && (
        <div>
          <h3>Blockers</h3>
          <ul className="list" aria-label="Readiness blockers">
            {blockers.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </div>
      )}
      {warnings.length > 0 && (
        <div>
          <h3>Warnings</h3>
          <ul className="list" aria-label="Readiness warnings">
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};
