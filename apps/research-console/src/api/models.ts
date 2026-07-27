export type HealthStatus = 'healthy' | 'degraded' | 'stale' | 'disconnected' | 'failed' | 'stopped';

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'failed';
  ready: boolean;
  blocking_reasons: string[];
  warnings: string[];
  version: string;
}

export interface ReadinessResponse {
  ready: boolean;
  blocking_reasons: string[];
  warnings: string[];
}

export interface ExperimentCreate {
  name: string;
  protocol_version_id?: string;
  parameters?: Record<string, unknown>;
  idempotency_key?: string;
}

export interface ExperimentResponse {
  id: string;
  name: string;
  protocol_version_id: string | null;
  parameters: Record<string, unknown>;
  created_at: number;
}

export interface ExperimentList {
  items: ExperimentResponse[];
}

export interface ProtocolReference {
  protocol_version_id: string;
  name: string;
  description: string;
}

export interface ProtocolList {
  items: ProtocolReference[];
}

export type RuntimeMode = 'replay' | 'synthetic_live' | 'fc11_live' | 'dry_run';
export type ApiMode = 'synthetic' | 'live' | 'replay';

export interface SessionCreate {
  experiment_id?: string;
  learner_id: string;
  mode: ApiMode;
  parameters?: Record<string, unknown>;
  protocol_version_id?: string;
  idempotency_key?: string;
}

export interface SessionResponse {
  id: string;
  experiment_id: string | null;
  learner_id: string;
  mode: string;
  status: string;
  protocol_version_id: string;
  created_at: number;
  updated_at: number;
}

export interface SessionList {
  items: SessionResponse[];
}

export interface SessionTransition {
  target: string;
  idempotency_key?: string;
}

export interface TransitionResponse {
  session_id: string;
  previous_status: string;
  status: string;
}

export interface SensorRegister {
  sensor_id: string;
  sensor_type?: string;
  idempotency_key?: string;
}

export interface SensorResponse {
  sensor_id: string;
  sensor_type: string;
  connected: boolean;
  session_id: string | null;
  lock_owner: string | null;
}

export interface SensorList {
  items: SensorResponse[];
}

export interface StimulusResponse {
  stimulus_id: string;
  label: string;
  source_text: string | null;
  tts_text: string | null;
  locale: string | null;
  duration_ms: number | null;
  available: boolean;
}

export interface StimulusList {
  items: StimulusResponse[];
}

export type ControlCommandName =
  | 'prepare'
  | 'start'
  | 'pause'
  | 'resume'
  | 'stop'
  | 'kill'
  | 'step'
  | 'force_baseline'
  | 'release_baseline'
  | 'freeze'
  | 'unfreeze';

export interface ControlCommand {
  command: ControlCommandName;
  idempotency_key?: string;
  parameters?: Record<string, unknown>;
}

export interface ControlResponse {
  session_id: string;
  command: string;
  status: string;
  details: Record<string, unknown>;
}

export interface EventSummary {
  event_id: string;
  event_type: string;
  session_sequence_number: number;
  timestamp: number;
  component: string;
}

export interface EventList {
  session_id: string;
  page: number;
  page_size: number;
  total: number;
  items: EventSummary[];
}

export interface ExportRequest {
  format: 'json' | 'jsonl' | 'csv' | 'manifest';
  idempotency_key?: string;
}

export interface ExportResponse {
  session_id: string;
  export_id: string;
  format: string;
  download_url: string;
  checksum: string;
  record_count: number;
  redacted: boolean;
}

export interface ExportManifest {
  session_id: string;
  record_count: number;
  event_export_checksum: string;
  summary_checksum: string;
  redacted: boolean;
  generated_at: number;
}

export interface ErrorResponse {
  code: string;
  message: string;
  request_id: string;
  resource_id: string | null;
  retryable: boolean;
  details: Record<string, unknown>;
}

export interface CausalLink {
  id: string;
  type: string;
  payload?: Record<string, unknown>;
  missing: boolean;
}

export interface CausalTrace {
  observationFrame?: CausalLink;
  cognitiveStateEstimate?: CausalLink;
  controlDecision?: CausalLink;
  actuationReceipt?: CausalLink;
  mantraControlState?: CausalLink;
  voiceAsset?: CausalLink;
  audioAsset?: CausalLink;
  utterancePlan?: CausalLink;
  renderedAudioArtifact?: CausalLink;
  playbackReceipt?: CausalLink;
  interventionOutcome?: CausalLink;
}

export interface HebrewStimulusMetadata {
  curriculum_item_id: string;
  lemma: string;
  root: string;
  binyan: string;
  tense: string;
  mood: string;
  person: string;
  gender: string;
  number: string;
  register: string;
  pointed_hebrew: string;
  italian_meaning: string;
  morphology_valid: boolean;
  pointing_provenance: string;
  help_references: string[];
  pronunciation_review_status: 'pending' | 'approved' | 'rejected';
  required_voice: string;
  cache_status: string;
  asset_checksum: string | null;
}

export const toApiMode = (runtime: RuntimeMode): ApiMode => {
  switch (runtime) {
    case 'fc11_live':
    case 'synthetic_live':
      return 'live';
    case 'replay':
      return 'replay';
    case 'dry_run':
    default:
      return 'synthetic';
  }
};
