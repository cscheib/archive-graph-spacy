"""Typed records for the local nlpdata pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

from archive_graph_spacy.models import Contact, Message


@dataclass(frozen=True)
class SourceBundle:
    contacts: tuple[Contact, ...]
    messages: tuple[Message, ...]
    reviewed_assertions: tuple[dict[str, object], ...] = ()
    review_assertion_decisions: tuple[dict[str, object], ...] = ()


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
    publish_diagnostics: dict[str, object] = field(default_factory=dict)

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
class CandidateAssertion:
    candidate_assertion_id: str
    run_id: str
    assertion_type: str
    subject_canonical_id: str
    proposed_claim: str
    evidence_refs: tuple[str, ...]
    provenance_summary: str
    confidence_level: float
    generation_scope: str
    generated_at: str
    review_class: str
    promotion_class: str

    def to_record(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True)
class CandidateDiagnosticsSummary:
    run_id: str
    generation_scope: str
    emitted_candidate_count: int
    candidate_counts_by_type: dict[str, int]
    suppressed_counts: dict[str, int]
    example_candidate_ids: tuple[str, ...]
    generated_at: str
    reviewed_effect_counts: dict[str, int] = field(default_factory=dict)

    def to_record(self) -> dict[str, object]:
        payload = asdict(self)
        payload["example_candidate_ids"] = list(self.example_candidate_ids)
        return payload


@dataclass(frozen=True)
class ReviewedEffectResult:
    run_id: str
    candidate_assertion_id: str
    assertion_type: str
    subject_canonical_id: str
    result: str
    reason_code: str
    details: str

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PersonPersonEdgeRecord:
    pair_id: str
    person_a_id: str
    person_b_id: str
    run_id: str
    generation_scope: str
    strength_score: float
    relationship_signal: str
    direct_evidence_count: int
    indirect_evidence_count: int
    strongest_evidence_ref: str
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PersonPersonEdgeEvidenceRecord:
    pair_evidence_id: str
    pair_id: str
    evidence_family: str
    source_ref: str
    contribution_score: float
    rank_within_pair: int
    message_ref: str
    theme_refs: tuple[str, ...] = ()
    provenance: str = ""

    def to_record(self) -> dict[str, object]:
        payload = asdict(self)
        payload["theme_refs"] = list(self.theme_refs)
        return payload


@dataclass(frozen=True)
class PhaseRecord:
    phase_id: str
    run_id: str
    generation_scope: str
    phase_index: int
    start_at: str
    end_at: str
    interaction_count: int
    representative_interaction_ref: str
    boundary_reason: str
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PhaseCentralPersonRecord:
    phase_id: str
    run_id: str
    person_id: str
    rank: int
    centrality_score: float
    interaction_count: int
    evidence_ref: str
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PhaseThemeSummaryRecord:
    phase_id: str
    run_id: str
    theme: str
    rank: int
    theme_score: float
    message_count: int
    evidence_ref: str
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PhasePairSummaryRecord:
    phase_pair_id: str
    phase_id: str
    pair_id: str
    run_id: str
    pair_rank: int
    activity_score: float
    relationship_signal: str
    evidence_count: int
    strongest_evidence_ref: str
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PhasePairEvidenceRecord:
    phase_pair_evidence_id: str
    phase_pair_id: str
    phase_id: str
    pair_id: str
    run_id: str
    source_ref: str
    message_ref: str
    evidence_family: str
    rank_within_phase_pair: int
    contribution_score: float
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PhaseRepresentativeInteractionRecord:
    phase_id: str
    run_id: str
    interaction_ref: str
    rank: int
    selection_reason: str
    is_current: bool = True

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PhaseDiagnosticsRecord:
    run_id: str
    phase_id: str
    diagnostic_type: str
    result: str
    reason_code: str
    sample_ref: str
    details: str

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
    candidate_assertions: tuple[CandidateAssertion, ...]
    candidate_summary: CandidateDiagnosticsSummary
    theme_tags: tuple[ThemeTag, ...]
    search_docs: tuple[SearchDocument, ...]
    reviewed_effects: tuple[ReviewedEffectResult, ...] = ()
    person_person_edges: tuple[PersonPersonEdgeRecord, ...] = ()
    person_person_edge_evidence: tuple[PersonPersonEdgeEvidenceRecord, ...] = ()
    phases: tuple[PhaseRecord, ...] = ()
    phase_central_people: tuple[PhaseCentralPersonRecord, ...] = ()
    phase_theme_summaries: tuple[PhaseThemeSummaryRecord, ...] = ()
    phase_pair_summaries: tuple[PhasePairSummaryRecord, ...] = ()
    phase_pair_evidence: tuple[PhasePairEvidenceRecord, ...] = ()
    phase_representative_interactions: tuple[PhaseRepresentativeInteractionRecord, ...] = ()
    phase_diagnostics: tuple[PhaseDiagnosticsRecord, ...] = ()
    suppressed_counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class PhaseRefreshResult:
    run: RefreshRun
    phases: tuple[PhaseRecord, ...] = ()
    phase_central_people: tuple[PhaseCentralPersonRecord, ...] = ()
    phase_theme_summaries: tuple[PhaseThemeSummaryRecord, ...] = ()
    phase_pair_summaries: tuple[PhasePairSummaryRecord, ...] = ()
    phase_pair_evidence: tuple[PhasePairEvidenceRecord, ...] = ()
    phase_representative_interactions: tuple[PhaseRepresentativeInteractionRecord, ...] = ()
    phase_diagnostics: tuple[PhaseDiagnosticsRecord, ...] = ()


@dataclass(frozen=True)
class BoundedPublishScope:
    run_id: str
    run_scope: str
    affected_message_ids: tuple[str, ...]
    overlap_class: str
    affected_identity_values: tuple[str, ...] = ()
    affected_tables: tuple[str, ...] = ()

    def to_record(self) -> dict[str, object]:
        payload = asdict(self)
        payload["affected_message_ids"] = list(self.affected_message_ids)
        payload["affected_identity_values"] = list(self.affected_identity_values)
        payload["affected_tables"] = list(self.affected_tables)
        return payload


@dataclass(frozen=True)
class PublishDiagnosticsRecord:
    run_id: str
    publish_scope: dict[str, object]
    publish_stage: str
    publish_outcome: str
    overlap_policy: str
    recovery_action: str
    staged_path: str
    finalized_tables: tuple[str, ...]
    failed_tables: tuple[str, ...]
    manual_intervention_required: bool
    job_id: str | None = None
    job_run_id: str | None = None
    parent_job_run_id: str | None = None
    task_run_id: str | None = None
    task_key: str | None = None
    task_name: str | None = None

    def to_record(self) -> dict[str, object]:
        payload = asdict(self)
        payload["finalized_tables"] = list(self.finalized_tables)
        payload["failed_tables"] = list(self.failed_tables)
        return payload
