import * as React from 'react';
import { useEffect, useState } from 'react';

import { api } from '../api/client';

export const ScientificValidationPage: React.FC = () => {
  const [studies, setStudies] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .listStudies()
      .then((res) => {
        if (!cancelled) {
          setStudies(res.items || []);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError('Unable to load studies.');
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="card" aria-label="Scientific validation">
      <h2>Scientific Validation</h2>
      {error && <p role="alert">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Study ID</th>
            <th>Title</th>
            <th>Status</th>
            <th>Primary Endpoint</th>
          </tr>
        </thead>
        <tbody>
          {studies.map((study) => (
            <tr key={String(study.study_id)}>
              <td>{String(study.study_id)}</td>
              <td>{String(study.title)}</td>
              <td>{String(study.status)}</td>
              <td>{String(study.primary_endpoint_id)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>Effect estimates and confidence intervals are shown in the analysis view.</p>
    </section>
  );
};
