# MPE Canonical Identifier Registry v1.1 (corrected)

## Status

This registry defines every identifier used across the MPE v1.1 package, the object that owns it, and where it is introduced. After the blocking correction pass, every object primary identifier is named canonically as `<object>_id` and every reference uses the same canonical name.

## Identifier definitions

| Identifier | Owner object | Introduced in | Referenced by | Format | Immutable target | Notes |
|---|---|---|---|---|---|---|
| `program_id` | `Program` | `MPE_OBJECT_MODEL_V1_1.md` §Program | `ProgramVersion` | UUID or slug | Yes | Logical identity only. |
| `program_version_id` | `ProgramVersion` | `MPE_OBJECT_MODEL_V1_1.md` §ProgramVersion | `Session`, `session_created`, `session_started` | UUID | Yes | Object model now defines `program_version_id` explicitly. |
| `protocol_id` | `Protocol` | `MPE_OBJECT_MODEL_V1_1.md` §Protocol | `ProtocolVersion` | UUID or slug | Yes | Logical identity only. |
| `protocol_version_id` | `ProtocolVersion` | `MPE_OBJECT_MODEL_V1_1.md` §ProtocolVersion | `Session`, `session_created`, `session_started`, `Event` common fields | UUID | Yes | Object model now defines `protocol_version_id` explicitly. |
| `session_id` | `Session` | `MPE_EVENT_MODEL_V1_1.md` `session_created` | All events | UUID | Yes | Consistent. |
| `block_id` | `Block` | `MPE_OBJECT_MODEL_V1_1.md` §Block | `block_started`, `block_completed`, `trial_created` | UUID | Yes | Consistent. |
| `task_definition_id` | `TaskDefinition` | `MPE_OBJECT_MODEL_V1_1.md` §TaskDefinition | `trial_created` | UUID | Yes | Consistent. |
| `trial_id` | `Trial` | `MPE_EVENT_MODEL_V1_1.md` `trial_created` | Instruction, stimulus, response, evaluation, feedback, schedule, adaptation events | UUID | Yes | Consistent. |
| `content_item_id` | `ContentItem` | `MPE_OBJECT_MODEL_V1_1.md` §ContentItem | `StimulusRequest`, `RenderedStimulus`, `Evaluation`, `FeedbackEvent`, `HebrewEvaluator` | UUID | Yes | `Trial` uses plural `content_item_ids`; consistent. |
| `stimulus_request_id` | `StimulusRequest` | `MPE_EVENT_MODEL_V1_1.md` `stimulus_requested` | `stimulus_ready`, `stimulus_started`, `stimulus_completed` | UUID | Yes | Consistent. |
| `rendered_stimulus_id` | `RenderedStimulus` | `MPE_EVENT_MODEL_V1_1.md` `stimulus_ready` | `stimulus_started`, `stimulus_completed` | UUID | Yes | Consistent. |
| `instruction_id` | `Instruction` | `MPE_EVENT_MODEL_V1_1.md` `instruction_started` | `instruction_completed` | UUID | Yes | Consistent. |
| `response_window_id` | `ResponseWindow` | `MPE_EVENT_MODEL_V1_1.md` `response_window_opened` | `response_detected`, `response_completed`, `response_timeout`, `observation_received` | UUID | Yes | Consistent. |
| `observation_id` | `Observation` | `MPE_OBJECT_MODEL_V1_1.md` §Observation | `response_detected`, `response_completed`, `CapturedResponse` | UUID | Yes | Renamed from generic `id` in object model. |
| `captured_response_id` | `CapturedResponse` | `MPE_OBJECT_MODEL_V1_1.md` §CapturedResponse | `ResponseInterpretation`, `captured_response_created` | UUID | Yes | Renamed from generic `id`; `captured_response_created` event introduced. |
| `response_interpretation_id` | `ResponseInterpretation` | `MPE_OBJECT_MODEL_V1_1.md` §ResponseInterpretation | `DomainNormalizedResponse`, `response_interpreted` | UUID | Yes | Renamed from generic `id`; `response_interpreted` event introduced. |
| `domain_normalized_response_id` | `DomainNormalizedResponse` | `MPE_OBJECT_MODEL_V1_1.md` §DomainNormalizedResponse | `Evaluation`, `domain_response_normalized` | UUID | Yes | Renamed from `normalized_response_id` and generic `id`; `response_normalized` renamed to `domain_response_normalized`. |
| `evaluation_id` | `Evaluation` | `MPE_OBJECT_MODEL_V1_1.md` §Evaluation | `evaluation_completed`, `evaluation_abstained`, `evaluation_failed`, `feedback_started`, `schedule_decision`, `adaptation_proposed` | UUID | Yes | Renamed from generic `id`. |
| `feedback_event_id` | `FeedbackEvent` | `MPE_OBJECT_MODEL_V1_1.md` §FeedbackEvent | `feedback_started`, `feedback_completed` | UUID | Yes | Renamed from generic `id`. |
| `safety_instruction_id` | `SafetyInstruction` | `MPE_OBJECT_MODEL_V1_1.md` §SafetyInstruction | `safety_instruction_started`, `safety_instruction_completed` | UUID | Yes | Renamed from generic `id`. |
| `adaptation_decision_id` | `AdaptationDecision` | `MPE_OBJECT_MODEL_V1_1.md` §AdaptationDecision | `adaptation_proposed`, `adaptation_abstained`, `adaptation_applied`, `adaptation_reversed` | UUID | Yes | Renamed from generic `id`. |
| `schedule_decision_id` | `ScheduleDecision` | `MPE_OBJECT_MODEL_V1_1.md` §ScheduleDecision | `schedule_decision`, `trial_created` | UUID | Yes | Renamed from generic `id`. |
| `state_estimate_id` | `StateEstimate` | `MPE_OBJECT_MODEL_V1_1.md` §StateEstimate | `state_estimate_produced` | UUID | Yes | Added to object model and event payload. |
| `sensor_observation_id` | `SensorObservation` | `MPE_OBJECT_MODEL_V1_1.md` §SensorObservation | `observation_received` (when `observation_type == sensor_feature`) | UUID | Yes | Renamed from generic `id`. |
| `safety_event_id` | `SafetyEvent` | `MPE_OBJECT_MODEL_V1_1.md` §SafetyEvent | `safety_rule_triggered`, `recovery_inserted`, `protocol_terminated` | UUID | Yes | Renamed from generic `id`; added to safety event payloads. |
| `evidence_record_id` | `EvidenceRecord` | `MPE_OBJECT_MODEL_V1_1.md` §EvidenceRecord | `evaluation_completed`, `evaluation_failed`, `schedule_decision`, `adaptation_proposed`, `evidence_record_created` | UUID | Yes | Renamed from generic `id`; `evidence_record_created` event introduced. |
| `policy_id` | `AdaptationDecision` | `MPE_OBJECT_MODEL_V1_1.md` §AdaptationDecision | `adaptation_*` events | string | Yes | Consistent with `policy_version`. |
| `scheduler_id` | `ScheduleDecision` | `MPE_OBJECT_MODEL_V1_1.md` §ScheduleDecision | `schedule_decision` | string | Yes | Consistent with `scheduler_version`. |
| `item_history_snapshot_id` | `ScheduleDecision` | `MPE_OBJECT_MODEL_V1_1.md` §ScheduleDecision | `schedule_decision` | UUID | Yes | Consistent. |
| `random_seed` | `Session` | `MPE_EVENT_MODEL_V1_1.md` `session_started` | `schedule_decision` (when applicable) | string/integer | Yes | Consistent. |
| `correlation_id` | `Event` common fields | `MPE_EVENT_MODEL_V1_1.md` §Event payload shape | All request/response events | UUID | Yes | Consistent. |
| `session_sequence_number` | `Event` common fields | `MPE_EVENT_MODEL_V1_1.md` §Event payload shape | All events | integer | Yes | Defines canonical per-session ordering. |

## Naming conventions

- All stable identifiers use `snake_case`.
- Every object primary identifier is named `<object>_id` in the object model and in every event/reference.
- Version identifiers pair with `*_version` (e.g., `protocol_version_id` + `version`).
- Logical identities (`Program`, `Protocol`) have `*_id`; executable versions have `*_version_id`.
- Event `event_id` is the event's own identity; it is never used as a canonical ordering key.

## Identifiers resolved by this correction pass

| Original issue | Resolution |
|---|---|
| `session_created` payload `program_id` vs `program_version_id` | Event payload now uses `program_version_id`. |
| `normalized_response_id` ambiguous | Renamed to `domain_normalized_response_id` everywhere. |
| `CapturedResponse.id` not named `captured_response_id` | Renamed. |
| `DomainNormalizedResponse.id` not named `domain_normalized_response_id` | Renamed. |
| `ResponseInterpretation.id` not named `response_interpretation_id` | Renamed. |
| Missing `session_sequence_number` | Added to common event fields. |
| `state_estimate_produced` event lacks `state_estimate_id` | Added. |
| `ProgramVersion`/`ProtocolVersion` lacked own `*_version_id` fields | Added `program_version_id` and `protocol_version_id`. |
