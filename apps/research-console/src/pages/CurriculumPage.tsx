import * as React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type {
  HebrewCurriculum,
  HebrewCurriculumReadiness,
  HebrewCurriculumUnit,
  HebrewCurriculumSkill,
  HebrewReadinessBlocker,
} from '../api/models';

const CurriculumPage: React.FC = () => {
  const [curriculum, setCurriculum] = useState<HebrewCurriculum | null>(null);
  const [readiness, setReadiness] = useState<HebrewCurriculumReadiness | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getHebrewCurriculum('clm06b-hebrew')
      .then((c) => setCurriculum(c))
      .catch(() => setError('Unable to load curriculum'));
    api
      .getHebrewCurriculumReadiness('clm06b-hebrew')
      .then((r) => setReadiness(r))
      .catch(() => setError('Unable to load readiness'));
  }, []);

  return (
    <div className="curriculum-page">
      <h2>CLM-06B Curriculum</h2>
      {error && <div role="alert">{error}</div>}
      {curriculum ? (
        <section className="card">
          <h3>Version</h3>
          <p>{curriculum.version}</p>
          <h3>Units</h3>
          <ul>
            {curriculum.units.map((u: HebrewCurriculumUnit) => (
              <li key={u.unit_id}>{u.title}</li>
            ))}
          </ul>
          <h3>Skills</h3>
          <ul>
            {curriculum.skills.map((s: HebrewCurriculumSkill) => (
              <li key={s.skill_id}>{s.label}</li>
            ))}
          </ul>
        </section>
      ) : (
        <p>Loading curriculum...</p>
      )}
      {readiness ? (
        <section className="card" aria-label="Curriculum readiness">
          <h3>Readiness</h3>
          <p>Ready: {readiness.ready ? 'Yes' : 'No'}</p>
          <p>Approved: {readiness.approved_count}</p>
          <p>Ready items: {readiness.ready_count}</p>
          {readiness.blockers.length > 0 && (
            <>
              <h4>Blockers</h4>
              <ul>
                {readiness.blockers.map((b: HebrewReadinessBlocker, i: number) => (
                  <li key={i}>{b.item_id ?? 'global'}: {b.blocker_type} — {b.detail}</li>
                ))}
              </ul>
            </>
          )}
          <h4>Asset Coverage</h4>
          <ul>
            {readiness.asset_report.slice(0, 10).map((entry, i) => (
              <li key={i}>
                {entry.required_asset}: {entry.present ? 'present' : 'missing'}
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <p>Loading readiness...</p>
      )}
    </div>
  );
};

export default CurriculumPage;
