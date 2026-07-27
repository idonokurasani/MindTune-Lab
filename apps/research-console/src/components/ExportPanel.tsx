import * as React from 'react';
import { useState } from 'react';
import { api } from '../api/client';
import type { ExportResponse } from '../api/models';

interface ExportPanelProps {
  sessionId: string;
}

const FORMATS = ['json', 'jsonl', 'csv', 'manifest'] as const;

export const ExportPanel: React.FC<ExportPanelProps> = ({ sessionId }) => {
  const [results, setResults] = useState<ExportResponse[]>([]);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const doExport = async (format: string) => {
    setLoading(format);
    setError(null);
    try {
      const response = await api.requestExport(sessionId, format);
      setResults((prev) => [...prev, response]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(null);
    }
  };

  return (
    <section className="card" aria-label="Export panel">
      <h2>Exports</h2>
      <div className="grid">
        {FORMATS.map((f) => (
          <button key={f} onClick={() => doExport(f)} disabled={loading === f}>
            Export {f.toUpperCase()}
          </button>
        ))}
      </div>
      {error && <p role="alert">{error}</p>}
      <ul className="list" aria-label="Export results">
        {results.map((r) => (
          <li key={r.export_id}>
            {r.format} — {r.record_count} records — checksum {r.checksum} — redacted: {r.redacted ? 'yes' : 'no'}
          </li>
        ))}
      </ul>
    </section>
  );
};
