import * as React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { HebrewCurriculum, HebrewCurriculumItem } from '../api/models';

const ItemInspectionPage: React.FC = () => {
  const [curriculum, setCurriculum] = useState<HebrewCurriculum | null>(null);
  const [selectedId, setSelectedId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getHebrewCurriculum('clm06b-hebrew')
      .then((c) => {
        setCurriculum(c);
        if (c.items.length > 0) {
          setSelectedId(c.items[0].item_id);
        }
      })
      .catch(() => setError('Unable to load items'));
  }, []);

  const selected = curriculum?.items.find((i: HebrewCurriculumItem) => i.item_id === selectedId);

  return (
    <div className="item-inspection-page">
      <h2>Item Inspection</h2>
      {error && <div role="alert">{error}</div>}
      {curriculum ? (
        <section className="card">
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            aria-label="Select curriculum item"
          >
            {curriculum.items.map((item: HebrewCurriculumItem) => (
              <option key={item.item_id} value={item.item_id}>
                {item.canonical_unpointed}
              </option>
            ))}
          </select>
          {selected && (
            <dl>
              <dt>Pointed</dt>
              <dd>{selected.canonical_pointed}</dd>
              <dt>Unpointed</dt>
              <dd>{selected.canonical_unpointed}</dd>
              <dt>Italian gloss</dt>
              <dd>{selected.italian_gloss}</dd>
              <dt>Provenance</dt>
              <dd>{selected.source_provenance}</dd>
              <dt>Validation status</dt>
              <dd>{selected.morphology_validation_status}</dd>
            </dl>
          )}
        </section>
      ) : (
        <p>Loading items...</p>
      )}
    </div>
  );
};

export default ItemInspectionPage;
