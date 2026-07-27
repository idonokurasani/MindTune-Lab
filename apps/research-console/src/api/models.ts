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
  calibration_profile_id?: string | null;
  calibration_profile_version?: string | null;
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

export interface HebrewItem {
  item_id: string;
  lemma: string;
  lemma_pointed: string;
  lemma_unpointed: string;
  root: string;
  binyan: string;
  tense: string;
  mood: string;
  person: string;
  gender: string;
  number: string;
  canonical_pointed: string;
  canonical_unpointed: string;
  transliteration: string;
  italian_gloss: string;
  natural_italian: string;
  morphology_provenance: string;
  pointing_provenance: string;
  help_references: string[];
  linguistic_validation_status: string;
  pronunciation_review_status: string;
  required_audio_asset_ids: string[];
}

export interface HebrewReadiness {
  ready: boolean;
  approved_count: number;
  ready_count: number;
  missing_assets: string[];
  blockers: string[];
}

export interface HebrewTrial {
  trial_id: string;
  presentation_id: string;
  prompt_id: string;
  item_id: string;
  trial_type: string;
  direction: string;
  prompt_text: string;
  pointed_hebrew: string;
  unpointed_hebrew: string;
  italian_meaning: string;
  choices: string[] | null;
  expected: string;
}

export interface HebrewResponseSubmit {
  response_text: string;
  response_time_ms?: number;
  confidence?: number;
  idempotency_key?: string;
}

export interface HebrewResponseResult {
  response: Record<string, unknown>;
  score: Record<string, unknown>;
  cognitive_state: string;
  control_state: Record<string, unknown>;
  playback_receipt: Record<string, unknown> | null;
  pedagogical_decision: Record<string, unknown>;
  next_trial: HebrewTrial | null;
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

export interface HebrewCurriculumSummary {
  curriculum_id: string;
  version: string;
  base_version: string;
}

export interface HebrewCurriculum {
  curriculum_id: string;
  version: string;
  base_version: string;
  source_provenance: string;
  metadata: Record<string, unknown>;
  units: HebrewCurriculumUnit[];
  lessons: HebrewCurriculumLesson[];
  skills: HebrewCurriculumSkill[];
  items: HebrewCurriculumItem[];
  prereq_graph: HebrewPrerequisiteEdge[];
  contrast_sets: HebrewContrastSet[];
}

export interface HebrewCurriculumUnit {
  unit_id: string;
  title: string;
  lesson_ids: string[];
  skill_ids: string[];
}

export interface HebrewCurriculumLesson {
  lesson_id: string;
  unit_id: string;
  title: string;
  item_ids: string[];
  skill_target_ids: string[];
}

export interface HebrewCurriculumSkill {
  skill_id: string;
  label: string;
  parent_skill_ids: string[];
  description: string;
}

export interface HebrewCurriculumItem {
  item_id: string;
  curriculum_version: string;
  unit_id: string;
  lesson_id: string;
  item_version: string;
  domain: string;
  skill_target_ids: string[];
  prerequisite_item_ids: string[];
  prerequisite_skill_ids: string[];
  difficulty_estimate: number;
  help_references: string[];
  morphology_validation_status: string;
  pointing_validation_status: string;
  pronunciation_review_status: string;
  active_learning_eligible: boolean;
  reference_only: boolean;
  accepted_alternatives: string[];
  confusion_set_ids: string[];
  source_provenance: string;
  deprecated: boolean;
  replacement_item_id: string | null;
  change_reason: string;
  canonical_pointed: string;
  canonical_unpointed: string;
  italian_gloss: string;
  natural_italian: string;
}

export interface HebrewPrerequisiteEdge {
  source_item_id: string;
  target_item_id: string;
  kind: string;
  edge_version: string;
}

export interface HebrewContrastSet {
  contrast_set_id: string;
  member_item_ids: string[];
  dimensions: string[];
  expected_confusion_types: string[];
  eligibility: string;
  progression_rule: string;
  review_rule: string;
  active: boolean;
}

export interface HebrewCurriculumReadiness {
  ready: boolean;
  approved_count: number;
  ready_count: number;
  blocked_items: string[];
  blockers: HebrewReadinessBlocker[];
  asset_report: HebrewAssetReadinessEntry[];
}

export interface HebrewReadinessBlocker {
  item_id: string | null;
  blocker_type: string;
  detail: string;
}

export interface HebrewAssetReadinessEntry {
  required_asset: string;
  present: boolean;
  voice: string;
  locale: string;
  pointed_request_checksum: string;
  pronunciation_review_status: string;
  cache_compatibility: string;
  historical_incompatibility_reason: string | null;
}

export interface HebrewLearnerState {
  learner_id: string;
  session_id: string;
  pinned_curriculum_version: string;
  item_states: Record<string, unknown>;
  skill_states: Record<string, unknown>;
  exposure_count: number;
  completed_item_ids: string[];
  deferred_item_ids: string[];
  blocked_item_ids: string[];
  active_difficulty: number;
  semantic_time: number;
}

export interface HebrewProgressionDecision {
  action: string;
  next_item_id: string | null;
  next_trial_type: string | null;
  assistance_delta: number;
  reason_codes: string[];
  repeat_same_item: boolean;
  interleave_item_id: string | null;
  review_scheduled: Record<string, unknown>;
  contrast_set_id: string | null;
  blocked: boolean;
}

export interface HebrewProgressionResponse {
  session_id: string;
  curriculum_version: string;
  current_item_id: string;
  decision: HebrewProgressionDecision;
  score?: Record<string, unknown>;
  idempotent?: boolean;
}

export interface CalibrationFeatureBaseline {
  feature_name: string;
  modality: string;
  unit: string;
  sample_count: number;
  accepted_count: number;
  rejected_count: number;
  missing_count: number;
  central_tendency: number;
  dispersion: number;
  robust_min: number;
  robust_max: number;
  selected_quantiles: Record<string, number>;
  outlier_policy: string;
  distribution_shape: Record<string, unknown>;
  stability_metrics: Record<string, number>;
  quality_status: string;
  transformation_recommendation: string;
  algorithm_version: string;
}

export type CalibrationProfileStatus =
  | 'collecting'
  | 'insufficient_data'
  | 'unstable'
  | 'valid'
  | 'degraded'
  | 'expired'
  | 'incompatible'
  | 'superseded'
  | 'invalid';

export interface CalibrationProfile {
  profile_id: string;
  profile_version: string;
  participant_id: string;
  sensor_family: string;
  sensor_config_fingerprint: string;
  feature_schema_version: string;
  validity_status: CalibrationProfileStatus;
  accepted_observation_count: number;
  rejected_observation_count: number;
  created_at: number;
  feature_baselines: Record<string, CalibrationFeatureBaseline>;
}

export interface CalibrationProfileList {
  items: CalibrationProfile[];
}

export interface CalibrationStatus {
  participant_id: string;
  total_profiles: number;
  valid_profiles: number;
  latest_profile_id: string | null;
}

export interface CalibrationSession {
  session_id: string;
  participant_id: string;
  protocol_id: string | null;
  protocol_version: string | null;
  status: string;
  created_at: number;
  updated_at: number;
  pinned_profile_id: string | null;
  pinned_profile_version: string | null;
}

export interface CalibrationSessionCreate {
  participant_id: string;
  protocol_id?: string;
  protocol_version?: string;
  sensor_family?: string;
  sensor_config_fingerprint?: string;
  parser_version?: string;
  feature_schema_version?: string;
  idempotency_key?: string;
}

export interface CalibrationSessionResponse extends CalibrationSession {}

export interface CalibrationSessionList {
  items: CalibrationSession[];
}

export interface CalibrationReadinessResponse {
  ready: boolean;
  blocking_reasons: string[];
  warnings: string[];
}

export interface CalibrationSummaryResponse {
  session_id: string;
  status: string;
  block_count: number;
  accepted: number;
  rejected: number;
  missing: number;
}

export interface CalibrationProfileAction {
  reason?: string;
  idempotency_key?: string;
}

export interface CalibrationSelectionResponse {
  profile_id: string | null;
  profile_version: string | null;
  reason: string;
}

export interface CalibrationHealthResponse {
  status: string;
  ready: boolean;
  blockers: string[];
  warnings: string[];
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
