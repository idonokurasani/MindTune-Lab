import * as React from 'react';
import { HealthPanel } from '../components/HealthPanel';
import { StatusBadge } from '../components/StatusBadge';
import type { HealthResponse } from '../api/models';

interface OverviewPageProps {
  health: HealthResponse | null;
  liveness: { status: string } | null;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ health, liveness }) => {
  return (
    <section aria-label="Overview">
      <h2>Overview</h2>
      <div className="card">
        <p>
          Liveness:{' '}
          <StatusBadge
            status={liveness?.status === 'ok' ? 'healthy' : 'failed'}
            label={liveness?.status ?? 'unknown'}
          />
        </p>
      </div>
      <HealthPanel health={health} />
    </section>
  );
};
