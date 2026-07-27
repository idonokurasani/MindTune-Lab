import * as React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { HebrewItem, HebrewResponseResult, HebrewTrial } from '../api/models';

const HebrewSessionPage: React.FC = () => {
  const [readiness, setReadiness] = useState<{
    ready: boolean;
    approved_count: number;
    ready_count: number;
    missing_assets: string[];
    blockers: string[];
  } | null>(null);
  const [items, setItems] = useState<HebrewItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<HebrewItem | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [trial, setTrial] = useState<HebrewTrial | null>(null);
  const [responseText, setResponseText] = useState('');
  const [lastResult, setLastResult] = useState<HebrewResponseResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.hebrewReadiness().then(setReadiness).catch(() => setError('Unable to load Hebrew readiness'));
    api.listHebrewItems().then((data) => setItems(data.items)).catch(() => setError('Unable to load Hebrew items'));
  }, []);

  const startSession = async () => {
    try {
      const data = await api.createHebrewSession();
      setSessionId(data.session_id);
      setError(null);
      const t = await api.getHebrewCurrentTrial(data.session_id);
      setTrial(t);
    } catch (err) {
      setError('Failed to start Hebrew session');
    }
  };

  const submitResponse = async () => {
    if (!sessionId || !trial) return;
    try {
      const result = await api.submitHebrewResponse(sessionId, trial.trial_id, {
        response_text: responseText,
        response_time_ms: 1200,
        confidence: 5,
      });
      setLastResult(result);
      setResponseText('');
      if (result.next_trial) {
        setTrial(result.next_trial);
      } else {
        setTrial(null);
      }
    } catch (err) {
      setError('Failed to submit response');
    }
  };

  return (
    <div className="hebrew-session-page">
      <h2>Hebrew Adaptive Session</h2>
      {error && <div className="error-banner" role="alert">{error}</div>}

      <section className="card">
        <h3>Readiness</h3>
        {readiness ? (
          <div>
            <p>Ready: {readiness.ready ? 'Yes' : 'No'}</p>
            <p>Approved items: {readiness.approved_count}</p>
            <p>Ready items: {readiness.ready_count}</p>
            {readiness.blockers.length > 0 && (
              <ul>
                {readiness.blockers.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
            )}
          </div>
        ) : (
          <p>Loading readiness...</p>
        )}
      </section>

      <section className="card">
        <h3>Validated Hebrew Items (read-only)</h3>
        <select
          onChange={(e) => {
            const item = items.find((i) => i.item_id === e.target.value) || null;
            setSelectedItem(item);
          }}
          value={selectedItem?.item_id || ''}
        >
          <option value="">Select an item</option>
          {items.map((item) => (
            <option key={item.item_id} value={item.item_id}>
              {item.lemma_unpointed} — {item.italian_gloss}
            </option>
          ))}
        </select>
        {selectedItem && (
          <dl>
            <dt>Pointed</dt>
            <dd>{selectedItem.canonical_pointed}</dd>
            <dt>Unpointed</dt>
            <dd>{selectedItem.canonical_unpointed}</dd>
            <dt>Root</dt>
            <dd>{selectedItem.root}</dd>
            <dt>Binyan</dt>
            <dd>{selectedItem.binyan}</dd>
            <dt>Tense</dt>
            <dd>{selectedItem.tense}</dd>
            <dt>Provenance</dt>
            <dd>{selectedItem.morphology_provenance}</dd>
          </dl>
        )}
      </section>

      <section className="card">
        <h3>Session</h3>
        <button onClick={startSession} disabled={!readiness?.ready}>
          Start Hebrew Session
        </button>
        {sessionId && <p>Session: {sessionId}</p>}
      </section>

      <section className="card">
        <h3>Current Trial</h3>
        {trial ? (
          <div>
            <p><strong>Prompt:</strong> {trial.prompt_text}</p>
            <p><strong>Pointed Hebrew:</strong> {trial.pointed_hebrew}</p>
            <p><strong>Italian meaning:</strong> {trial.italian_meaning}</p>
            <input
              type="text"
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              placeholder="Type Hebrew response"
              aria-label="Hebrew response"
            />
            <button onClick={submitResponse}>Submit</button>
          </div>
        ) : (
          <p>No active trial.</p>
        )}
      </section>

      {lastResult && (
        <section className="card">
          <h3>Feedback</h3>
          <p>Overall: {String(lastResult.score?.overall)}</p>
          <p>Cognitive state: {lastResult.cognitive_state}</p>
          <p>Next action: {String(lastResult.pedagogical_decision?.action)}</p>
        </section>
      )}
    </div>
  );
};

export default HebrewSessionPage;
