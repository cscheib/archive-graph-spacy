"""Typed records for the local nlpdata pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

from archive_graph_spacy.models import Contact, Message


@dataclass(frozen=True)
class SourceBundle:
    contacts: tuple[Contact, ...]
    messages: tuple[Message, ...]


@dataclass(frozen=True)
class RefreshRun:
    run_id: str
    run_scope: str
    source_catalog: str
    started_at: datetime
    completed_at: datetime
    status: str
    input_interaction_count: int
    output_row_counts: dict[str, int]
    quality_metrics: dict[str, int | float | bool]

    def to_record(self) -> dict[str, object]:
        payload = asdict(self)
        payload["started_at"] = self.started_at.isoformat()
        payload["completed_at"] = self.completed_at.isoformat()
        return payload


@dataclass(frozen=True)
class InteractionMention:
    mention_id: str
    run_id: str
    message_id: str
    source_interaction_id: str
    span_text: str
    label: str
    start_char: int
    end_char: int
    source_type: str
    confidence: float

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PersonMessageLink:
    link_id: str
    run_id: str
    message_id: str
    person_id: str
    person_name: str
    role: str
    link_origin: str
    confidence: float
    evidence_type: str
    evidence_value: str
    source_interaction_id: str
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ThemeTag:
    theme_tag_id: str
    run_id: str
    message_id: str
    theme: str
    confidence: float
    evidence: str
    source_method: str
    source_interaction_id: str
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SearchDocument:
    message_id: str
    run_id: str
    source_interaction_id: str
    source_type: str
    timestamp: str | None
    subject_terms: tuple[str, ...]
    body_terms: tuple[str, ...]
    linked_person_ids: tuple[str, ...]
    linked_person_names: tuple[str, ...]
    explicit_person_ids: tuple[str, ...]
    inferred_person_ids: tuple[str, ...]
    theme_labels: tuple[str, ...]
    time_facets: dict[str, str]
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        payload = asdict(self)
        for key in (
            "subject_terms",
            "body_terms",
            "linked_person_ids",
            "linked_person_names",
            "explicit_person_ids",
            "inferred_person_ids",
            "theme_labels",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True)
class PipelineResult:
    run: RefreshRun
    mentions: tuple[InteractionMention, ...]
    person_links: tuple[PersonMessageLink, ...]
    theme_tags: tuple[ThemeTag, ...]
    search_docs: tuple[SearchDocument, ...]
    suppressed_counts: dict[str, int] = field(default_factory=dict)
