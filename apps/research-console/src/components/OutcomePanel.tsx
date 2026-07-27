import * as React from 'react';
interface OutcomePanelProps {
  outcome?: { status: string; level: number; tempo_ratio: number; pause_duration_ms: number } | null;
}

export const OutcomePanel: React.FC<OutcomePanelProps> = ({ outcome }) => {
  const status = outcome?.status ?? '—';
  const level = outcome?.level ?? '—';
  const tempo = outcome?.tempo_ratio ?? '—';
  const pause = outcome?.pause_duration_ms ?? '—';
  return (
    <section className="card" aria-label="Outcome panel">
      <h2>Outcome</h2>
      <dl className="readonly-meta">
        <dt>Status</dt>
        <dd>{status}</dd>
        <dt>Intervention level</dt>
        <dd>{level}</dd>
        <dt>Tempo ratio</dt>
        <dd>{tempo}</dd>
        <dt>Pause duration (ms)</dt>
        <dd>{pause}</dd>
      </dl>
    </section>
  );
};
