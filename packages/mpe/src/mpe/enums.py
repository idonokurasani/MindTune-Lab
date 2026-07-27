"""Canonical enum values and state transition rules for MPE v1.1."""

from __future__ import annotations

from enum import Enum


class CanonicalEnum(str, Enum):
    """Base class for canonical MPE string enums."""

    @classmethod
    def values(cls) -> list[str]:
        return [m.value for m in cls]

    @classmethod
    def validate(
        cls, value: str | "CanonicalEnum" | None, required: bool = True
    ) -> "CanonicalEnum" | None:
        if value is None:
            if required:
                raise ValueError(f"{cls.__name__} is required")
            return None
        if isinstance(value, cls):
            return value
        if isinstance(value, CanonicalEnum):
            value = value.value
        if value not in cls._value2member_map_:
            raise ValueError(f"Invalid {cls.__name__}: {value!r}; expected one of {cls.values()}")
        return cls(value)


class SessionStatus(CanonicalEnum):
    """Session lifecycle status."""

    CREATED = "created"
    STARTED = "started"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"


class BlockType(CanonicalEnum):
    """Block type."""

    INSTRUCTION = "instruction"
    TRIAL = "trial"
    PRACTICE = "practice"
    REST = "rest"


class ResponseRequirement(CanonicalEnum):
    """Whether a response is required, optional, or not expected."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    NONE = "none"


class ResponseMode(CanonicalEnum):
    """Allowed response capture modes."""

    TYPED = "typed"
    SPOKEN = "spoken"
    TOUCH = "touch"
    GESTURE = "gesture"
    KEYBOARD = "keyboard"
    NONE = "none"


class AnswerStatus(CanonicalEnum):
    """Evaluation result for a response."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    ACCEPTABLE_VARIANT = "acceptable_variant"
    PARTIALLY_CORRECT = "partially_correct"
    UNEVALUABLE = "unevaluable"


class EvaluationStatus(CanonicalEnum):
    """Whether an evaluation completed and its outcome."""

    COMPLETED = "completed"
    ABSTAINED = "abstained"
    FAILED = "failed"
    OUT_OF_SCOPE = "out_of_scope"


class ScopeStatus(CanonicalEnum):
    """Scope status for evaluation."""

    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"


class DecisionType(CanonicalEnum):
    """Scheduler decision type."""

    NEXT_TRIAL = "next_trial"
    BLOCK_START = "block_start"
    BLOCK_END = "block_end"
    SESSION_END = "session_end"
    PAUSE = "pause"
    ABORT = "abort"


class DecisionStatus(CanonicalEnum):
    """Scheduler decision status."""

    MADE = "made"
    PENDING_CONFIRMATION = "pending_confirmation"
    REJECTED = "rejected"
    OVERRIDDEN = "overridden"
    ABSTAINED = "abstained"


class ObservationType(CanonicalEnum):
    """Observation type."""

    TYPED_INPUT = "typed_input"
    AUDIO_INPUT = "audio_input"
    TOUCH_INPUT = "touch_input"
    GESTURE_INPUT = "gesture_input"
    KEYBOARD_INPUT = "keyboard_input"
    EYE_GAZE = "eye_gaze"
    EEG_BURST = "eeg_burst"


class InterpretationType(CanonicalEnum):
    """Interpretation type."""

    TYPED_TEXT = "typed_text"
    TRANSCRIBED_TEXT = "transcribed_text"
    RAW_TOUCH = "raw_touch"
    RAW_GESTURE = "raw_gesture"
    BUTTON_LABEL = "button_label"
    SELECTED_OPTION = "selected_option"


class InstructionType(CanonicalEnum):
    """Type of instruction."""

    PRESENT_STIMULUS = "PRESENT_STIMULUS"
    INSTRUCT_COVERT_RETRIEVAL = "INSTRUCT_COVERT_RETRIEVAL"
    INSTRUCT_COVERT_REHEARSAL = "INSTRUCT_COVERT_REHEARSAL"
    INSTRUCT_IMAGERY = "INSTRUCT_IMAGERY"
    REQUEST_OVERT_RESPONSE = "REQUEST_OVERT_RESPONSE"
    REQUEST_CONFIDENCE_RATING = "REQUEST_CONFIDENCE_RATING"
    REQUEST_SELF_REPORT = "REQUEST_SELF_REPORT"
    DELIVER_SAFETY_INSTRUCTION = "DELIVER_SAFETY_INSTRUCTION"


class FeedbackCategory(CanonicalEnum):
    """Category of feedback."""

    KNOWLEDGE = "KNOWLEDGE"
    PERFORMANCE = "PERFORMANCE"
    METACOGNITIVE = "METACOGNITIVE"


class FeedbackType(CanonicalEnum):
    """Type of feedback."""

    CORRECT_ANSWER = "correct_answer"
    INCORRECT_INDICATOR = "incorrect_indicator"
    ELABORATION = "elaboration"


class ErrorCategory(CanonicalEnum):
    """Category of provider/evaluator failure."""

    TIMEOUT = "timeout"
    RENDERER_FAILURE = "renderer_failure"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    VALIDATION_FAILURE = "validation_failure"
    EVALUATION_FAILURE = "evaluation_failure"
    UNKNOWN = "unknown"


class DeploymentStatus(CanonicalEnum):
    """Deployment status for adaptations and experimental signals."""

    EXPLORATORY_ONLY = "exploratory_only"
    SHADOW_MODE = "shadow_mode"
    LIMITED_RUNTIME = "limited_runtime"
    PRODUCTION_APPROVED = "production_approved"


class AdaptationDecision(CanonicalEnum):
    """Decision for whether to apply an adaptation."""

    APPLY = "APPLY"
    NO_CHANGE_INSUFFICIENT_EVIDENCE = "NO_CHANGE_INSUFFICIENT_EVIDENCE"
    REVERSE = "REVERSE"
    ABSTAIN = "ABSTAIN"


class TransferClaimLevel(CanonicalEnum):
    """Transfer claim level for protocols."""

    TRAINED_TASK_PERFORMANCE = "trained_task_performance"
    ITEM_GENERALIZATION = "item_generalization"
    NEAR_TRANSFER = "near_transfer"
    FAR_TRANSFER = "far_transfer"
    CLINICAL_OUTCOME = "clinical_outcome"


class ProtocolPurpose(CanonicalEnum):
    """Purpose of a cognitive protocol."""

    ASSESSMENT = "assessment"
    ACQUISITION = "acquisition"
    RETRIEVAL = "retrieval"
    CONSOLIDATION = "consolidation"
    GENERALIZATION = "generalization"
    REGULATION = "regulation"
    REHABILITATION = "rehabilitation"
    MIXED = "mixed"


class TaskFamily(CanonicalEnum):
    """Task family classification."""

    OVERT_RECALL = "overt_recall"
    OVERT_RECOGNITION = "overt_recognition"
    COVERT_RETRIEVAL = "covert_retrieval"
    COVERT_REHEARSAL = "covert_rehearsal"
    IMAGERY = "imagery"
    SELF_REPORT = "self_report"


class DataClassification(CanonicalEnum):
    """Data classification for event payloads."""

    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CONSENT_GATED = "consent_gated"
    SENSITIVE_PHI = "sensitive_phi"


# Valid session lifecycle transitions
SESSION_TRANSITIONS: dict[SessionStatus | None, set[SessionStatus]] = {
    None: {SessionStatus.CREATED},
    SessionStatus.CREATED: {
        SessionStatus.STARTED,
        SessionStatus.CANCELLED,
        SessionStatus.TERMINATED,
    },
    SessionStatus.STARTED: {
        SessionStatus.PAUSED,
        SessionStatus.COMPLETED,
        SessionStatus.CANCELLED,
        SessionStatus.TERMINATED,
    },
    SessionStatus.PAUSED: {
        SessionStatus.RESUMED,
        SessionStatus.CANCELLED,
        SessionStatus.TERMINATED,
    },
    SessionStatus.RESUMED: {
        SessionStatus.PAUSED,
        SessionStatus.COMPLETED,
        SessionStatus.CANCELLED,
        SessionStatus.TERMINATED,
    },
    SessionStatus.COMPLETED: set(),
    SessionStatus.CANCELLED: set(),
    SessionStatus.TERMINATED: set(),
}
