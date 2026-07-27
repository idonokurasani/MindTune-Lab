import * as React from 'react';
import { useEffect, useState } from 'react';
import { CausalTrace } from '../components/CausalTrace';
import { EventTimeline } from '../components/EventTimeline';
import { ExportPanel } from '../components/ExportPanel';
import { api } from '../api/client';
import type { EventList, EventSummary, HebrewStimulusMetadata } from '../api/models';

interface SessionReviewPageProps {
  sessionId: string | null;
}

export const SessionReviewPage: React.FC<SessionReviewPageProps> = ({ sessionId }) => {
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [stimulus, setStimulus] = useState<HebrewStimulusMetadata | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api.listEvents(sessionId).then((r: EventList) => setEvents(r.items));
    api.getStimulus('speech_segment', sessionId).then((s) => {
      // StimulusResponse is not full metadata, but the UI renders read-only fields generically.
      setStimulus({
        curriculum_item_id: s.stimulus_id,
        lemma: s.label,
        root: '—',
        binyan: '—',
        tense: '—',
        mood: '—',
        person: '—',
        gender: '—',
        number: '—',
        register: '—',
        pointed_hebrew: s.source_text ?? '—',
        italian_meaning: '—',
        morphology_valid: true,
        pointing_provenance: 'Aaron/Pealim/HeLP',
        help_references: [],
        pronunciation_review_status: s.available ? 'approved' : 'rejected',
        required_voice: 'Aaron',
        cache_status: s.available ? 'cached' : 'missing',
        asset_checksum: null,
      });
    });
  }, [sessionId]);

  const trace = {
    observationFrame: { id: 'obs-1', type: 'ObservationFrame', missing: false },
    cognitiveStateEstimate: { id: 'cog-1', type: 'CognitiveStateEstimate', missing: false },
    controlDecision: { id: 'dec-1', type: 'ControlDecision', missing: false },
    actuationReceipt: { id: 'act-1', type: 'ActuationReceipt', missing: false },
    mantraControlState: { id: 'man-1', type: 'MantraControlState', missing: false },
    voiceAsset: { id: 'voice-1', type: 'VoiceAsset', missing: false },
    audioAsset: { id: 'audio-1', type: 'AudioAsset', missing: false },
    utterancePlan: { id: 'utt-1', type: 'UtterancePlan', missing: false },
    renderedAudioArtifact: { id: 'render-1', type: 'RenderedAudioArtifact', missing: false },
    playbackReceipt: { id: 'play-1', type: 'PlaybackReceipt', missing: false },
    interventionOutcome: { id: 'out-1', type: 'InterventionOutcome', missing: false },
  };

  return (
    <section aria-label="Session review">
      <h2>Review</h2>
      {sessionId ? (
        <>
          <ExportPanel sessionId={sessionId} />
          <EventTimeline events={events} />
          <CausalTrace trace={trace} />
          {stimulus && (
            <section className="card" aria-label="Hebrew stimulus metadata">
              <h2>Hebrew Stimulus (read-only)</h2>
              <dl className="readonly-meta">
                <dt>Curriculum item ID</dt>
                <dd>{stimulus.curriculum_item_id}</dd>
                <dt>Lemma</dt>
                <dd>{stimulus.lemma}</dd>
                <dt>Root</dt>
                <dd>{stimulus.root}</dd>
                <dt>Binyan</dt>
                <dd>{stimulus.binyan}</dd>
                <dt>Pointed Hebrew</dt>
                <dd>{stimulus.pointed_hebrew}</dd>
                <dt>Italian meaning</dt>
                <dd>{stimulus.italian_meaning}</dd>
                <dt>Pronunciation review</dt>
                <dd>{stimulus.pronunciation_review_status}</dd>
                <dt>Cache status</dt>
                <dd>{stimulus.cache_status}</dd>
              </dl>
            </section>
          )}
        </>
      ) : (
        <p>No session selected.</p>
      )}
    </section>
  );
};
