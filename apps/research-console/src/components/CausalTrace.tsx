import * as React from 'react';
import type { CausalTrace as CausalTraceData, CausalLink } from '../api/models';

const STEPS: { key: keyof CausalTraceData; label: string }[] = [
  { key: 'observationFrame', label: 'ObservationFrame' },
  { key: 'cognitiveStateEstimate', label: 'CognitiveStateEstimate' },
  { key: 'controlDecision', label: 'ControlDecision' },
  { key: 'actuationReceipt', label: 'ActuationReceipt' },
  { key: 'mantraControlState', label: 'MantraControlState' },
  { key: 'voiceAsset', label: 'VoiceAsset' },
  { key: 'audioAsset', label: 'AudioAsset' },
  { key: 'utterancePlan', label: 'UtterancePlan' },
  { key: 'renderedAudioArtifact', label: 'RenderedAudioArtifact' },
  { key: 'playbackReceipt', label: 'PlaybackReceipt' },
  { key: 'interventionOutcome', label: 'InterventionOutcome' },
];

const LinkView: React.FC<{ label: string; link?: CausalLink }> = ({ label, link }) => {
  if (!link || link.missing) {
    return (
      <li className="list" aria-label={`${label} missing`}>
        {label}: <em>missing</em>
      </li>
    );
  }
  return (
    <li className="list">
      {label}: <code>{link.id}</code> ({link.type})
    </li>
  );
};

export const CausalTrace: React.FC<{ trace: CausalTraceData }> = ({ trace }) => {
  return (
    <section className="card" aria-label="Causal trace">
      <h2>Causal Trace</h2>
      <ol className="list">
        {STEPS.map((s) => (
          <LinkView key={s.key} label={s.label} link={trace[s.key]} />
        ))}
      </ol>
    </section>
  );
};
