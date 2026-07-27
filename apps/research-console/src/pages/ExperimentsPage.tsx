import * as React from 'react';
import { useState } from 'react';
import { sanitizeNotes } from '../api/client';
import type { ExperimentCreate, ExperimentResponse, ProtocolReference } from '../api/models';

interface ExperimentsPageProps {
  experiments: ExperimentResponse[];
  protocols: ProtocolReference[];
  onCreate: (data: ExperimentCreate) => void;
  onDelete: (id: string) => void;
}

export const ExperimentsPage: React.FC<ExperimentsPageProps> = ({
  experiments,
  protocols,
  onCreate,
  onDelete,
}) => {
  const [name, setName] = useState('');
  const [protocol, setProtocol] = useState(protocols[0]?.protocol_version_id ?? '');
  const [params, setParams] = useState('{}');

  const handleCreate = () => {
    let parsed: Record<string, unknown> = {};
    try {
      parsed = JSON.parse(params);
    } catch {
      // ignore
    }
    onCreate({
      name: sanitizeNotes(name),
      protocol_version_id: protocol,
      parameters: parsed,
    });
    setName('');
  };

  return (
    <section aria-label="Experiments">
      <h2>Experiments</h2>
      <div className="card">
        <div className="form-group">
          <label htmlFor="exp-name">Experiment name</label>
          <input id="exp-name" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="exp-protocol">Protocol version</label>
          <select id="exp-protocol" value={protocol} onChange={(e) => setProtocol(e.target.value)}>
            {protocols.map((p) => (
              <option key={p.protocol_version_id} value={p.protocol_version_id}>
                {p.name} ({p.protocol_version_id})
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="exp-params">Parameters (JSON)</label>
          <textarea id="exp-params" value={params} onChange={(e) => setParams(e.target.value)} />
        </div>
        <button onClick={handleCreate}>Create Experiment</button>
      </div>
      <ul className="list" aria-label="Experiments list">
        {experiments.map((e) => (
          <li key={e.id}>
            <strong>{e.name}</strong> — {e.protocol_version_id} — created {new Date(e.created_at * 1000).toLocaleString()}
            <button onClick={() => onDelete(e.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </section>
  );
};
