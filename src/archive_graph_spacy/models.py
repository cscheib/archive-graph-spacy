"""Core data structures for archive experiments."""

from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Contact:
    person_id: str
    display_name: str
    emails: tuple[str, ...] = ()
    phones: tuple[str, ...] = ()
    photo_url: str | None = None
    entity_type: str = "unknown"


@dataclass(frozen=True)
class Message:
    message_id: str
    source: str
    sender: str
    recipients: tuple[str, ...]
    subject: str
    body: str
    timestamp: datetime | None = None
    interaction_type: str | None = None


@dataclass(frozen=True)
class Mention:
    text: str
    label: str
    source: str


@dataclass(frozen=True)
class LinkCandidate:
    person_id: str
    score: float
    reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PersonMessageEdgeEvidence:
    edge_id: str
    person_id: str
    message_id: str
    role: str
    evidence_type: str
    evidence_value: str
    confidence: float
    source: str


@dataclass(frozen=True)
class PersonMessageEdge:
    edge_id: str
    person_id: str
    message_id: str
    role: str
    confidence: float
    source: str
    strongest_evidence_type: str
    strongest_evidence_value: str
    evidence_count: int


@dataclass(frozen=True)
class PersonPersonEdgeEvidence:
    edge_id: str
    person_a_id: str
    person_b_id: str
    message_id: str
    relationship_type: str
    confidence: float
    source: str


@dataclass(frozen=True)
class PersonPersonEdge:
    edge_id: str
    person_a_id: str
    person_b_id: str
    confidence: float
    message_count: int
    co_participant_count: int
    mention_count: int
    strongest_relationship_type: str
    strongest_message_id: str
