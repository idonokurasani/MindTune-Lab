import * as React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { HebrewLearnerState, HebrewProgressionResponse } from '../api/models';

const LearnerProgressionPage: React.FC = () => {
  const [state, setState] = useState<HebrewLearnerState | null>(null);
  const [progression, setProgression] = useState<HebrewProgressionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getHebrewLearnerState('console-progression')
      .then((s) => setState(s))
      .catch(() => setError('Unable to load learner state'));
    api
      .getHebrewProgression('console-progression')
      .then((p) => setProgression(p))
      .catch(() => setError('Unable to load progression'));
  }, []);

  return (
    <div className="learner-progression-page">
      <h2>Learner Progression</h2>
      {error && <div role="alert">{error}</div>}
      {state ? (
        <section className="card">
          <h3>Session</h3>
          <p>Curriculum version: {state.pinned_curriculum_version}</p>
          <p>Completed items: {state.completed_item_ids.length}</p>
          <p>Blocked items: {state.blocked_item_ids.length}</p>
          <p>Deferred items: {state.deferred_item_ids.length}</p>
        </section>
      ) : (
        <p>Loading learner state...</p>
      )}
      {progression ? (
        <section className="card" aria-label="Progression decision">
          <h3>Progression Decision</h3>
          <p>Current item: {progression.current_item_id}</p>
          <p>Action: {progression.decision.action}</p>
          <p>Next item: {progression.decision.next_item_id ?? '—'}</p>
          <p>Assistance delta: {progression.decision.assistance_delta}</p>
        </section>
      ) : (
        <p>Loading progression...</p>
      )}
    </div>
  );
};

export default LearnerProgressionPage;
