"""Static fixture definitions for the Phase 4B.1 mock protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.enums import (
    BlockType,
    ProtocolPurpose,
    TaskFamily,
    TransferClaimLevel,
)
from mpe.providers import ContentItem
from mpe.types import (
    BlockID,
    ContentItemID,
    ProgramID,
    ProgramVersionID,
    ProtocolID,
    ProtocolVersionID,
    TaskDefinitionID,
)


@dataclass(frozen=True)
class Program:
    program_id: str
    name: str
    description: str = ""
    transfer_claim_level: str = TransferClaimLevel.TRAINED_TASK_PERFORMANCE.value


@dataclass(frozen=True)
class ProgramVersion:
    program_version_id: str
    program_id: str
    version: str
    checksum: str
    protocol_version_sequence: list[str]
    safety_profile_id: str | None = None
    consent_requirements: list[str] = field(default_factory=list)
    schema_version: str = "1.1"
    created_at: float = 0.0
    dependency_versions: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Protocol:
    protocol_id: str
    name: str
    protocol_family: str
    purpose: str
    description: str = ""
    default_transfer_claim: str | None = None


@dataclass(frozen=True)
class Block:
    block_id: str
    block_type: str
    trial_sequence: list[str] = field(default_factory=list)
    max_trials: int | None = None
    exit_condition: str | None = None


@dataclass(frozen=True)
class ProtocolVersion:
    protocol_version_id: str
    protocol_id: str
    version: str
    checksum: str
    objective: str
    purpose: str
    primary_transfer_claim: str
    block_sequence: list[Block] | None = None
    trial_sequence: list[str] | None = None
    required_providers: list[str] = field(default_factory=list)
    safety_profile_id: str | None = None
    schema_version: str = "1.1"
    dependency_versions: dict[str, str] = field(default_factory=dict)
    created_at: float = 0.0


@dataclass(frozen=True)
class TaskDefinition:
    task_definition_id: str
    version: str
    task_family: str
    trial_role_sequence: list[str]
    example_protocol_ids: list[str] = field(default_factory=list)


def make_mock_fixtures() -> dict[str, Any]:
    """Return a fully wired mock protocol fixture set."""
    program_id = str(ProgramID("mock_program"))
    program_version_id = str(ProgramVersionID("mock_program_version"))
    protocol_id = str(ProtocolID("mock_protocol"))
    protocol_version_id = str(ProtocolVersionID("mock_protocol_version"))
    task_definition_id = str(TaskDefinitionID("mock_overt_recall"))
    block_id = str(BlockID("mock_block_1"))
    content_item_id = str(ContentItemID("mock_item_1"))

    content_item = ContentItem(
        content_item_id=content_item_id,
        provider_id="mock_provider",
        provider_version="1.0.0",
        content_type="mock_word",
        checksum="mock_checksum",
        surface_form="mockanswer",
        normalized_form="mockanswer",
        status="verified_consensus",
    )

    program = Program(
        program_id=program_id,
        name="Mock Program",
        transfer_claim_level=TransferClaimLevel.TRAINED_TASK_PERFORMANCE.value,
    )

    program_version = ProgramVersion(
        program_version_id=program_version_id,
        program_id=program_id,
        version="1.0.0",
        checksum="program_checksum",
        protocol_version_sequence=[protocol_version_id],
        schema_version="1.1",
        dependency_versions={},
    )

    protocol = Protocol(
        protocol_id=protocol_id,
        name="Mock Protocol",
        protocol_family="mock",
        purpose=ProtocolPurpose.ASSESSMENT.value,
    )

    task_definition = TaskDefinition(
        task_definition_id=task_definition_id,
        version="1.0.0",
        task_family=TaskFamily.OVERT_RECALL.value,
        trial_role_sequence=["STIMULUS", "RESPONSE_WINDOW", "KNOWLEDGE_FEEDBACK"],
    )

    block = Block(
        block_id=block_id,
        block_type=BlockType.PRACTICE.value,
        trial_sequence=[content_item_id],
        max_trials=1,
        exit_condition="N_TRIALS_COMPLETED",
    )

    protocol_version = ProtocolVersion(
        protocol_version_id=protocol_version_id,
        protocol_id=protocol_id,
        version="1.0.0",
        checksum="protocol_checksum",
        objective="Mock reference execution for Phase 4B.1",
        purpose=ProtocolPurpose.ASSESSMENT.value,
        primary_transfer_claim=TransferClaimLevel.TRAINED_TASK_PERFORMANCE.value,
        block_sequence=[block],
        required_providers=[
            "mock_renderer",
            "mock_keyboard",
            "mock_interpreter",
            "mock_normalizer",
            "mock_evaluator",
            "mock_scheduler",
        ],
        dependency_versions={
            "mock_renderer": "1.0.0",
            "mock_keyboard": "1.0.0",
            "mock_interpreter": "1.0.0",
            "mock_normalizer": "1.0.0",
            "mock_evaluator": "1.0.0",
            "mock_scheduler": "1.0.0",
        },
        schema_version="1.1",
    )

    return {
        "program": program,
        "program_version": program_version,
        "protocol": protocol,
        "protocol_version": protocol_version,
        "task_definition": task_definition,
        "block": block,
        "content_item": content_item,
    }
