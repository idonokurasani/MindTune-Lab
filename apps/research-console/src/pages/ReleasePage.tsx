import * as React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { ReleaseInfo, ReleaseManifest, ReleaseValidation, ReleaseLimitations, ReleaseEvidence } from '../api/models';

export const ReleasePage: React.FC = () => {
  const [info, setInfo] = useState<ReleaseInfo | null>(null);
  const [manifest, setManifest] = useState<ReleaseManifest | null>(null);
  const [validation, setValidation] = useState<ReleaseValidation | null>(null);
  const [limitations, setLimitations] = useState<ReleaseLimitations | null>(null);
  const [evidence, setEvidence] = useState<ReleaseEvidence | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.getRelease(),
      api.getReleaseManifest(),
      api.getReleaseValidation(),
      api.getReleaseLimitations(),
      api.getReleaseEvidence(),
    ])
      .then(([i, m, v, l, e]) => {
        setInfo(i);
        setManifest(m);
        setValidation(v);
        setLimitations(l);
        setEvidence(e);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <section aria-label="Release Candidate">
      <h2>Release Candidate</h2>
      {error && <p className="error">Error loading release data: {error}</p>}
      {info && (
        <div className="card">
          <h3>Identity</h3>
          <ul className="list">
            <li>Version: {info.semantic_version}</li>
            <li>Release ID: <code>{info.release_id}</code></li>
            <li>Git SHA: <code>{info.git_commit_sha}</code></li>
            <li>Base SHA: <code>{info.base_sha}</code></li>
            <li>Dirty tree: {info.dirty_tree ? 'yes' : 'no'}</li>
            <li>Build timestamp: {info.build_timestamp}</li>
            <li>Status: {info.status}</li>
          </ul>
        </div>
      )}
      {validation && (
        <div className="card">
          <h3>Validation</h3>
          <p>Validation status: <strong>{validation.status}</strong></p>
          <p>Hardware tests: {validation.hardware_tests}</p>
          <p>Matrix: <code>{validation.validation_matrix_path}</code></p>
        </div>
      )}
      {evidence && (
        <div className="card">
          <h3>Evidence</h3>
          <p>Index: <code>{evidence.evidence_index}</code></p>
          <p>Status: {evidence.status}</p>
        </div>
      )}
      {limitations && (
        <div className="card">
          <h3>Known Limitations</h3>
          {limitations.known_limitations.length === 0 ? (
            <p>No limitations indexed in live manifest.</p>
          ) : (
            <ul className="list">
              {limitations.known_limitations.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          )}
          <p>Full list: <code>{limitations.limitations_path}</code></p>
        </div>
      )}
      {manifest && (
        <div className="card">
          <h3>Manifest</h3>
          <details>
            <summary>View full manifest</summary>
            <pre>{JSON.stringify(manifest, null, 2)}</pre>
          </details>
        </div>
      )}
    </section>
  );
};
