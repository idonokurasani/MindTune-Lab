"""Deterministic timeline compilation for a Mantra specification."""

# ruff: noqa: C901
from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .sheva import tts_variant
from .spec import MantraForm, MantraSpecification
from .utils import canonical_json, normalize_unicode, sha256_hex


class SegmentType(str, Enum):
    """Stable segment type vocabulary."""

    OPENING_SILENCE = "opening_silence"
    CLOSING_SILENCE = "closing_silence"
    ITALIAN_CUE = "italian_cue"
    ITALIAN_CUE_PAUSE = "italian_cue_pause"
    GRAMMATICAL_LABEL = "grammatical_label"
    HEBREW_INFINITIVE = "hebrew_infinitive"
    HEBREW_FORM = "hebrew_form"
    INTRA_FORM_SILENCE = "intra_form_silence"
    INTER_FORM_SILENCE = "inter_form_silence"
    GROUP_PAUSE = "group_pause"
    CYCLE_PAUSE = "cycle_pause"


@dataclass
class TimelineSegment:
    """One ordered segment in the compiled mantra timeline."""

    segment_id: str
    segment_type: SegmentType
    source_text: str
    vocalized_text: str
    grammatical_metadata: dict[str, Any]
    repetition_index: int
    cycle_index: int
    group_index: int
    form_index: int
    planned_start_time: float
    planned_duration: float
    tts_text: str = ""
    provider: str = ""
    language: str = ""
    locale: str = ""
    voice: str = ""
    artifact_reference: str | None = None
    generation_status: str = "pending"
    checksum: str | None = None
    actual_duration: float | None = None
    format: str = "wav"

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "segment_type": self.segment_type.value,
            "source_text": self.source_text,
            "vocalized_text": self.vocalized_text,
            "tts_text": self.tts_text,
            "grammatical_metadata": self.grammatical_metadata,
            "repetition_index": self.repetition_index,
            "cycle_index": self.cycle_index,
            "group_index": self.group_index,
            "form_index": self.form_index,
            "planned_start_time": self.planned_start_time,
            "planned_duration": self.planned_duration,
            "provider": self.provider,
            "language": self.language,
            "locale": self.locale,
            "voice": self.voice,
            "artifact_reference": self.artifact_reference,
            "generation_status": self.generation_status,
            "checksum": self.checksum,
            "actual_duration": self.actual_duration,
            "format": self.format,
        }


def _stable_segment_id(
    segment_type: SegmentType,
    source_text: str,
    cycle_index: int,
    group_index: int,
    form_index: int,
    repetition_index: int,
    build_seed: str,
) -> str:
    """Return a deterministic UUIDv5 segment identifier."""
    key = canonical_json(
        {
            "type": segment_type.value,
            "text": normalize_unicode(source_text),
            "cycle": cycle_index,
            "group": group_index,
            "form": form_index,
            "rep": repetition_index,
            "seed": build_seed,
        }
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"mantra://segment/{sha256_hex(key)}"))


def _speech_planned_duration(spec: MantraSpecification, text: str) -> float:
    """Estimate planned speech duration from text length and speech rate."""
    if not text:
        return 0.0
    return max(0.2, len(normalize_unicode(text))) * spec.base_seconds_per_char()


def _silence_segment(
    spec: MantraSpecification,
    segment_type: SegmentType,
    duration_ms: int,
    cycle_index: int,
    group_index: int,
    form_index: int,
    repetition_index: int,
    current_time: float,
) -> TimelineSegment:
    seg = TimelineSegment(
        segment_id=_stable_segment_id(
            segment_type,
            "",
            cycle_index,
            group_index,
            form_index,
            repetition_index,
            spec.build_seed,
        ),
        segment_type=segment_type,
        source_text="",
        vocalized_text="",
        grammatical_metadata={"duration_ms": duration_ms},
        repetition_index=repetition_index,
        cycle_index=cycle_index,
        group_index=group_index,
        form_index=form_index,
        planned_start_time=current_time,
        planned_duration=duration_ms / 1000.0,
        provider="silence",
        language="",
        locale="",
        voice="",
        generation_status="complete",
        format="pcm",
    )
    return seg


def _speech_segment(
    spec: MantraSpecification,
    segment_type: SegmentType,
    source_text: str,
    vocalized_text: str,
    form: MantraForm | None,
    group: Any | None,
    cycle_index: int,
    group_index: int,
    form_index: int,
    repetition_index: int,
    current_time: float,
) -> TimelineSegment:
    text = source_text or ""
    meta: dict[str, Any] = {}
    if form is not None and group is not None:
        meta = {
            "form_key": form.form_key,
            "tense": group.tense,
            "person": form.person,
            "number": form.number,
            "gender": form.gender,
            "stress_syllable_index": form.effective_stress(),
            "pronunciation_override": form.pronunciation_override,
            "sheva_annotations": [a.to_dict() for a in form.sheva_annotations],
            "tts_omit_silent": tts_variant(
                form.hebrew_with_niqqud, form.sheva_annotations, "omit_silent"
            ),
        }
    is_italian = segment_type in {SegmentType.ITALIAN_CUE, SegmentType.GRAMMATICAL_LABEL}
    speech_cfg = spec.italian_speech if is_italian else spec.speech
    tts_text = form.effective_tts_input() if form is not None else text
    seg = TimelineSegment(
        segment_id=_stable_segment_id(
            segment_type,
            text,
            cycle_index,
            group_index,
            form_index,
            repetition_index,
            spec.build_seed,
        ),
        segment_type=segment_type,
        source_text=text,
        vocalized_text=normalize_unicode(vocalized_text or text),
        tts_text=normalize_unicode(tts_text),
        grammatical_metadata=meta,
        repetition_index=repetition_index,
        cycle_index=cycle_index,
        group_index=group_index,
        form_index=form_index,
        planned_start_time=current_time,
        planned_duration=_speech_planned_duration(spec, text),
        provider=speech_cfg.provider,
        language=speech_cfg.language,
        locale=speech_cfg.locale,
        voice=speech_cfg.voice,
        generation_status="pending",
        format=speech_cfg.format,
    )
    return seg


def compile_timeline(spec: MantraSpecification) -> list[TimelineSegment]:  # noqa
    """Compile a deterministic ordered timeline from a Mantra specification."""
    timeline: list[TimelineSegment] = []
    current_time = 0.0

    # Opening silence
    timeline.append(
        _silence_segment(
            spec,
            SegmentType.OPENING_SILENCE,
            spec.pauses.opening_ms,
            0,
            0,
            0,
            0,
            current_time,
        )
    )
    current_time += spec.pauses.opening_ms / 1000.0

    for cycle_index in range(spec.cycles):
        for rep_cycle in range(spec.repetitions_per_cycle):
            for group_index, group in enumerate(spec.groups):
                if spec.include_grammatical_labels and group.label_he:
                    timeline.append(
                        _speech_segment(
                            spec,
                            SegmentType.GRAMMATICAL_LABEL,
                            group.label_he,
                            group.label_he,
                            None,
                            group,
                            cycle_index,
                            group_index,
                            -1,
                            rep_cycle,
                            current_time,
                        )
                    )
                    current_time += _speech_planned_duration(spec, group.label_he)
                    timeline.append(
                        _silence_segment(
                            spec,
                            SegmentType.ITALIAN_CUE_PAUSE,
                            spec.pauses.italian_cue_pause_ms,
                            cycle_index,
                            group_index,
                            -1,
                            rep_cycle,
                            current_time,
                        )
                    )
                    current_time += spec.pauses.italian_cue_pause_ms / 1000.0

                for form_index, form in enumerate(group.forms):
                    for form_rep in range(spec.repetitions_per_form):
                        if spec.include_italian_cue and form.italian_gloss:
                            timeline.append(
                                _speech_segment(
                                    spec,
                                    SegmentType.ITALIAN_CUE,
                                    form.italian_gloss,
                                    form.italian_gloss,
                                    form,
                                    group,
                                    cycle_index,
                                    group_index,
                                    form_index,
                                    form_rep,
                                    current_time,
                                )
                            )
                            current_time += _speech_planned_duration(spec, form.italian_gloss)
                            timeline.append(
                                _silence_segment(
                                    spec,
                                    SegmentType.ITALIAN_CUE_PAUSE,
                                    spec.pauses.italian_cue_pause_ms,
                                    cycle_index,
                                    group_index,
                                    form_index,
                                    form_rep,
                                    current_time,
                                )
                            )
                            current_time += spec.pauses.italian_cue_pause_ms / 1000.0

                        timeline.append(
                            _speech_segment(
                                spec,
                                SegmentType.HEBREW_FORM,
                                form.hebrew_with_niqqud,
                                form.vocalized,
                                form,
                                group,
                                cycle_index,
                                group_index,
                                form_index,
                                form_rep,
                                current_time,
                            )
                        )
                        current_time += _speech_planned_duration(spec, form.effective_tts_input())

                        if form_rep < spec.repetitions_per_form - 1:
                            timeline.append(
                                _silence_segment(
                                    spec,
                                    SegmentType.INTRA_FORM_SILENCE,
                                    spec.pauses.segment_pause_ms,
                                    cycle_index,
                                    group_index,
                                    form_index,
                                    form_rep,
                                    current_time,
                                )
                            )
                            current_time += spec.pauses.segment_pause_ms / 1000.0

                    # Inter-form silence after each form
                    timeline.append(
                        _silence_segment(
                            spec,
                            SegmentType.INTER_FORM_SILENCE,
                            spec.pauses.between_forms_ms,
                            cycle_index,
                            group_index,
                            form_index,
                            form_rep,
                            current_time,
                        )
                    )
                    current_time += spec.pauses.between_forms_ms / 1000.0

                # Group pause (except after last group of last cycle repetition)
                if group_index < len(spec.groups) - 1 or rep_cycle < spec.repetitions_per_cycle - 1:
                    timeline.append(
                        _silence_segment(
                            spec,
                            SegmentType.GROUP_PAUSE,
                            spec.pauses.between_groups_ms,
                            cycle_index,
                            group_index,
                            len(group.forms) - 1,
                            rep_cycle,
                            current_time,
                        )
                    )
                    current_time += spec.pauses.between_groups_ms / 1000.0

        # Cycle pause between cycles
        if cycle_index < spec.cycles - 1:
            timeline.append(
                _silence_segment(
                    spec,
                    SegmentType.CYCLE_PAUSE,
                    spec.pauses.between_cycles_ms,
                    cycle_index,
                    len(spec.groups) - 1,
                    0,
                    0,
                    current_time,
                )
            )
            current_time += spec.pauses.between_cycles_ms / 1000.0

    # Closing silence
    timeline.append(
        _silence_segment(
            spec,
            SegmentType.CLOSING_SILENCE,
            spec.pauses.closing_ms,
            0,
            0,
            0,
            0,
            current_time,
        )
    )

    return timeline
