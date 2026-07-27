import * as React from 'react';
import type { StimulusResponse } from '../api/models';

interface AudioPanelProps {
  stimuli: StimulusResponse[];
}

export const AudioPanel: React.FC<AudioPanelProps> = ({ stimuli }) => {
  return (
    <section className="card" aria-label="Audio panel">
      <h2>Audio / Stimuli</h2>
      <ul className="list" aria-label="Stimulus list">
        {stimuli.map((s) => (
          <li key={s.stimulus_id}>
            <strong>{s.label}</strong> ({s.stimulus_id})
            <br />
            Locale: {s.locale ?? '—'}; Duration: {s.duration_ms ?? '—'} ms; Available: {s.available ? 'yes' : 'no'}
          </li>
        ))}
      </ul>
    </section>
  );
};
