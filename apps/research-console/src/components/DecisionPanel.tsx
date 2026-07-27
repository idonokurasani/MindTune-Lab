import * as React from 'react';
interface DecisionPanelProps {
  requestedState?: string;
  appliedState?: string;
  fallbackReason?: string;
}

export const DecisionPanel: React.FC<DecisionPanelProps> = ({
  requestedState,
  appliedState,
  fallbackReason,
}) => {
  return (
    <section className="card" aria-label="Decision panel">
      <h2>Decision State</h2>
      <dl className="readonly-meta">
        <dt>Requested</dt>
        <dd>{requestedState ?? '—'}</dd>
        <dt>Applied</dt>
        <dd>{appliedState ?? '—'}</dd>
        <dt>Fallback reason</dt>
        <dd>{fallbackReason ?? '—'}</dd>
      </dl>
    </section>
  );
};
