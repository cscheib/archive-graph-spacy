"""Pipeline orchestration for local nlpdata derivation."""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from archive_graph_spacy.edges.person_person import build_nlpdata_person_person_outputs
from archive_graph_spacy.models import Message

from .contracts import TABLE_CONTRACTS
from .models import (
    PhaseCentralPersonRecord,
    PhaseDiagnosticsRecord,
    PhasePairEvidenceRecord,
    PhasePairSummaryRecord,
    PhaseRecord,
    PhaseRepresentativeInteractionRecord,
    PhaseThemeSummaryRecord,
    PipelineResult,
    PersonMessageLink,
    PersonPersonEdgeEvidenceRecord,
    PersonPersonEdgeRecord,
    SourceBundle,
    ThemeTag,
)
from .person_links import apply_reviewed_feedback, derive_candidate_assertions, derive_person_links
from .runs import (
    build_phase_quality_metrics,
    build_refresh_run,
    meets_runtime_goal,
    new_run_id,
    utc_now,
)
from .search_docs import build_search_documents
from .source_loader import load_source_bundle
from .themes import derive_theme_tags

RETAIN_BOUNDARY_DAYS = 45
MERGED_BOUNDARY_DAYS = 14
MIN_PHASE_INTERACTIONS = 2
MAX_REPRESENTATIVE_INTERACTIONS_PER_PHASE = 3
MAX_CENTRAL_PEOPLE_PER_PHASE = 5
MAX_THEME_SUMMARIES_PER_PHASE = 5
MAX_PHASE_PAIR_EVIDENCE_PER_PAIR = 5
MAX_PHASE_PAIR_EVIDENCE_PER_PHASE = 5
MAX_BOUNDARY_DIAGNOSTICS = 12


def _phase_id(generation_scope: str, message_ids: tuple[str, ...]) -> str:
    digest = hashlib.sha1(f"{generation_scope}|{'|'.join(message_ids)}".encode("utf-8")).hexdigest()[:12]
    return f"phase-{digest}"


def _phase_pair_id(phase_id: str, pair_id: str) -> str:
    digest = hashlib.sha1(f"{phase_id}|{pair_id}".encode("utf-8")).hexdigest()[:12]
    return f"phase-pair-{digest}"


def _phase_pair_evidence_id(phase_pair_id: str, source_ref: str, evidence_family: str) -> str:
    digest = hashlib.sha1(f"{phase_pair_id}|{source_ref}|{evidence_family}".encode("utf-8")).hexdigest()[:12]
    return f"phase-ppe-{digest}"


def _rebuild_candidate_summary(
    original_summary: object,
    *,
    candidate_assertions: tuple,
    reviewed_effects: tuple,
) -> object:
    candidate_counts: dict[str, int] = defaultdict(int)
    for candidate in candidate_assertions:
        candidate_counts[candidate.assertion_type] += 1
    reviewed_effect_counts: dict[str, int] = defaultdict(int)
    for effect in reviewed_effects:
        reviewed_effect_counts[effect.result] += 1
    return original_summary.__class__(
        run_id=original_summary.run_id,
        generation_scope=original_summary.generation_scope,
        emitted_candidate_count=len(candidate_assertions),
        candidate_counts_by_type=dict(candidate_counts),
        suppressed_counts=original_summary.suppressed_counts,
        example_candidate_ids=tuple(candidate.candidate_assertion_id for candidate in candidate_assertions[:5]),
        generated_at=original_summary.generated_at,
        reviewed_effect_counts=dict(reviewed_effect_counts),
    )


def _sorted_messages_with_timestamps(messages: tuple[Message, ...]) -> tuple[Message, ...]:
    def _normalized_timestamp(message: Message) -> datetime:
        assert message.timestamp is not None
        timestamp = message.timestamp
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=UTC)
        return timestamp.astimezone(UTC)

    return tuple(
        sorted(
            (message for message in messages if message.timestamp is not None),
            key=lambda message: (_normalized_timestamp(message), message.message_id),
        )
    )


def _derive_phase_outputs(
    *,
    messages: tuple[Message, ...],
    person_links: tuple[PersonMessageLink, ...],
    theme_tags: tuple[ThemeTag, ...],
    person_person_edges: tuple[PersonPersonEdgeRecord, ...],
    person_person_edge_evidence: tuple[PersonPersonEdgeEvidenceRecord, ...],
    run_id: str,
    generation_scope: str,
) -> tuple[
    tuple[PhaseRecord, ...],
    tuple[PhaseCentralPersonRecord, ...],
    tuple[PhaseThemeSummaryRecord, ...],
    tuple[PhasePairSummaryRecord, ...],
    tuple[PhasePairEvidenceRecord, ...],
    tuple[PhaseRepresentativeInteractionRecord, ...],
    tuple[PhaseDiagnosticsRecord, ...],
    dict[str, int],
]:
    sorted_messages = _sorted_messages_with_timestamps(messages)
    if not sorted_messages:
        return (), (), (), (), (), (), (), {
            "suppressed_phase_count": 0,
            "phase_boundary_merged_count": 0,
            "phase_boundary_retained_count": 0,
            "phase_representative_interaction_cap": MAX_REPRESENTATIVE_INTERACTIONS_PER_PHASE,
            "phase_pair_evidence_cap": MAX_PHASE_PAIR_EVIDENCE_PER_PAIR,
            "phase_pair_evidence_phase_cap": MAX_PHASE_PAIR_EVIDENCE_PER_PHASE,
            "phase_boundary_diagnostic_cap": MAX_BOUNDARY_DIAGNOSTICS,
        }

    link_by_message: dict[str, list[PersonMessageLink]] = defaultdict(list)
    for link in person_links:
        link_by_message[link.message_id].append(link)
    theme_by_message: dict[str, list[ThemeTag]] = defaultdict(list)
    for tag in theme_tags:
        theme_by_message[tag.message_id].append(tag)
    evidence_by_message: dict[str, list[PersonPersonEdgeEvidenceRecord]] = defaultdict(list)
    for row in person_person_edge_evidence:
        evidence_by_message[row.message_ref].append(row)
    pair_ids = {row.pair_id for row in person_person_edges}

    retained_boundary_indexes: set[int] = set()
    diagnostics: list[PhaseDiagnosticsRecord] = []
    boundary_candidates: list[tuple[str, float, str]] = []
    merged_count = 0
    retained_count = 0
    for index, (left, right) in enumerate(zip(sorted_messages, sorted_messages[1:]), start=1):
        assert left.timestamp is not None and right.timestamp is not None
        left_ts = left.timestamp.replace(tzinfo=UTC) if left.timestamp.tzinfo is None else left.timestamp.astimezone(UTC)
        right_ts = right.timestamp.replace(tzinfo=UTC) if right.timestamp.tzinfo is None else right.timestamp.astimezone(UTC)
        gap_days = (right_ts - left_ts).total_seconds() / 86400
        if gap_days >= RETAIN_BOUNDARY_DAYS:
            retained_boundary_indexes.add(index)
            retained_count += 1
            boundary_candidates.append(("retained", gap_days, right.message_id))
        elif gap_days >= MERGED_BOUNDARY_DAYS:
            merged_count += 1
            boundary_candidates.append(("merged", gap_days, right.message_id))

    segments: list[tuple[Message, ...]] = []
    current_segment: list[Message] = []
    for index, message in enumerate(sorted_messages):
        current_segment.append(message)
        if index + 1 in retained_boundary_indexes:
            segments.append(tuple(current_segment))
            current_segment = []
    if current_segment:
        segments.append(tuple(current_segment))
    segment_phase_ids = {
        segment[0].message_id: _phase_id(generation_scope, tuple(message.message_id for message in segment))
        for segment in segments
    }
    boundary_phase_ids: dict[str, str] = {}
    previous_published_phase_id: str | None = None
    for segment in segments:
        phase_id = segment_phase_ids[segment[0].message_id]
        if len(segment) >= MIN_PHASE_INTERACTIONS:
            previous_published_phase_id = phase_id
        boundary_phase_id = previous_published_phase_id or phase_id
        for message in segment:
            boundary_phase_ids[message.message_id] = boundary_phase_id
    bounded_boundary_candidates = sorted(
        boundary_candidates,
        key=lambda item: item[1],
        reverse=True,
    )[:MAX_BOUNDARY_DIAGNOSTICS]
    for result, gap_days, right_message_id in bounded_boundary_candidates:
        diagnostics.append(
            PhaseDiagnosticsRecord(
                run_id=run_id,
                phase_id=boundary_phase_ids[right_message_id],
                diagnostic_type="boundary",
                result=result,
                reason_code=f"gap_{result}",
                sample_ref=f"message:{right_message_id}",
                details=f"{result} boundary after {gap_days:.3f} day gap",
            )
        )

    phases: list[PhaseRecord] = []
    phase_central_people: list[PhaseCentralPersonRecord] = []
    phase_theme_summaries: list[PhaseThemeSummaryRecord] = []
    phase_pair_summaries: list[PhasePairSummaryRecord] = []
    phase_pair_evidence: list[PhasePairEvidenceRecord] = []
    phase_representative_interactions: list[PhaseRepresentativeInteractionRecord] = []
    suppressed_phase_count = 0

    for segment in segments:
        phase_id = segment_phase_ids[segment[0].message_id]
        if len(segment) < MIN_PHASE_INTERACTIONS:
            suppressed_phase_count += 1
            diagnostics.append(
                PhaseDiagnosticsRecord(
                    run_id=run_id,
                    phase_id=phase_id,
                    diagnostic_type="suppression",
                    result="suppressed",
                    reason_code="low_interaction_count",
                    sample_ref=f"message:{segment[0].message_id}",
                    details=f"suppressed weak segment with {len(segment)} interaction(s)",
                )
            )
            continue

        scored_messages = sorted(
            (
                (
                    len(link_by_message.get(message.message_id, ())) + len(theme_by_message.get(message.message_id, ())),
                    message.timestamp.isoformat() if message.timestamp else "",
                    message,
                )
                for message in segment
            ),
            key=lambda item: (-item[0], item[1], item[2].message_id),
        )
        representative = scored_messages[0][2]
        phases.append(
            PhaseRecord(
                phase_id=phase_id,
                run_id=run_id,
                generation_scope=generation_scope,
                phase_index=len(phases) + 1,
                start_at=segment[0].timestamp.isoformat(),
                end_at=segment[-1].timestamp.isoformat(),
                interaction_count=len(segment),
                representative_interaction_ref=f"message:{representative.message_id}",
                boundary_reason="time_gap_segmentation",
                is_current=True,
            )
        )
        for rank, (_, _, message) in enumerate(scored_messages[:MAX_REPRESENTATIVE_INTERACTIONS_PER_PHASE], start=1):
            phase_representative_interactions.append(
                PhaseRepresentativeInteractionRecord(
                    phase_id=phase_id,
                    run_id=run_id,
                    interaction_ref=f"message:{message.message_id}",
                    rank=rank,
                    selection_reason="top_phase_activity",
                    is_current=True,
                )
            )

        person_scores: dict[str, dict[str, object]] = {}
        for message in segment:
            for link in link_by_message.get(message.message_id, ()):
                stats = person_scores.setdefault(
                    link.person_id,
                    {"score": 0.0, "count": 0, "evidence_ref": f"message:{message.message_id}"},
                )
                weight = 2.0 if link.role in {"sender", "recipient"} else 1.0
                stats["score"] = float(stats["score"]) + weight * link.confidence
                stats["count"] = int(stats["count"]) + 1
        ordered_people = sorted(
            person_scores.items(),
            key=lambda item: (-float(item[1]["score"]), -int(item[1]["count"]), item[0]),
        )
        for rank, (person_id, stats) in enumerate(ordered_people[:MAX_CENTRAL_PEOPLE_PER_PHASE], start=1):
            phase_central_people.append(
                PhaseCentralPersonRecord(
                    phase_id=phase_id,
                    run_id=run_id,
                    person_id=person_id,
                    rank=rank,
                    centrality_score=round(float(stats["score"]), 6),
                    interaction_count=int(stats["count"]),
                    evidence_ref=str(stats["evidence_ref"]),
                    is_current=True,
                )
            )
        if ordered_people:
            diagnostics.append(
                PhaseDiagnosticsRecord(
                    run_id=run_id,
                    phase_id=phase_id,
                    diagnostic_type="central_people",
                    result="retained",
                    reason_code="bounded_ranking",
                    sample_ref=f"person:{ordered_people[0][0]}",
                    details=f"published {min(len(ordered_people), MAX_CENTRAL_PEOPLE_PER_PHASE)} central people",
                )
            )

        theme_scores: dict[str, dict[str, object]] = {}
        for message in segment:
            for tag in theme_by_message.get(message.message_id, ()):
                stats = theme_scores.setdefault(
                    tag.theme,
                    {"score": 0.0, "count": 0, "evidence_ref": f"message:{message.message_id}"},
                )
                stats["score"] = float(stats["score"]) + tag.confidence
                stats["count"] = int(stats["count"]) + 1
        ordered_themes = sorted(
            theme_scores.items(),
            key=lambda item: (-float(item[1]["score"]), -int(item[1]["count"]), item[0]),
        )
        for rank, (theme, stats) in enumerate(ordered_themes[:MAX_THEME_SUMMARIES_PER_PHASE], start=1):
            phase_theme_summaries.append(
                PhaseThemeSummaryRecord(
                    phase_id=phase_id,
                    run_id=run_id,
                    theme=theme,
                    rank=rank,
                    theme_score=round(float(stats["score"]), 6),
                    message_count=int(stats["count"]),
                    evidence_ref=str(stats["evidence_ref"]),
                    is_current=True,
                )
            )
        if ordered_themes:
            diagnostics.append(
                PhaseDiagnosticsRecord(
                    run_id=run_id,
                    phase_id=phase_id,
                    diagnostic_type="themes",
                    result="retained",
                    reason_code="bounded_ranking",
                    sample_ref=f"theme:{ordered_themes[0][0]}",
                    details=f"published {min(len(ordered_themes), MAX_THEME_SUMMARIES_PER_PHASE)} dominant themes",
                )
            )

        segment_pair_rows: dict[str, list[PersonPersonEdgeEvidenceRecord]] = defaultdict(list)
        for message in segment:
            for row in evidence_by_message.get(message.message_id, ()):
                if row.pair_id in pair_ids:
                    segment_pair_rows[row.pair_id].append(row)
        ordered_pairs: list[tuple[str, float, list[PersonPersonEdgeEvidenceRecord]]] = []
        for pair_id, rows in segment_pair_rows.items():
            rows.sort(key=lambda row: (-row.contribution_score, row.message_ref, row.evidence_family))
            ordered_pairs.append((pair_id, sum(row.contribution_score for row in rows), rows))
        ordered_pairs.sort(key=lambda item: (-item[1], item[0]))
        emitted_phase_pair_evidence = 0
        emitted_phase_pair_summaries = 0
        for pair_id, activity_score, rows in ordered_pairs:
            if emitted_phase_pair_evidence >= MAX_PHASE_PAIR_EVIDENCE_PER_PHASE:
                break
            phase_pair_id = _phase_pair_id(phase_id, pair_id)
            strongest = rows[0]
            emitted_phase_pair_summaries += 1
            phase_pair_summaries.append(
                PhasePairSummaryRecord(
                    phase_pair_id=phase_pair_id,
                    phase_id=phase_id,
                    pair_id=pair_id,
                    run_id=run_id,
                    pair_rank=emitted_phase_pair_summaries,
                    activity_score=round(activity_score, 6),
                    relationship_signal=strongest.evidence_family,
                    evidence_count=len(rows),
                    strongest_evidence_ref=strongest.source_ref,
                    is_current=True,
                )
            )
            bounded_rows = rows[:MAX_PHASE_PAIR_EVIDENCE_PER_PAIR]
            for evidence_rank, row in enumerate(bounded_rows, start=1):
                if emitted_phase_pair_evidence >= MAX_PHASE_PAIR_EVIDENCE_PER_PHASE:
                    break
                phase_pair_evidence.append(
                    PhasePairEvidenceRecord(
                        phase_pair_evidence_id=_phase_pair_evidence_id(phase_pair_id, row.source_ref, row.evidence_family),
                        phase_pair_id=phase_pair_id,
                        phase_id=phase_id,
                        pair_id=pair_id,
                        run_id=run_id,
                        source_ref=row.source_ref,
                        message_ref=row.message_ref,
                        evidence_family=row.evidence_family,
                        rank_within_phase_pair=evidence_rank,
                        contribution_score=row.contribution_score,
                        is_current=True,
                    )
                )
                emitted_phase_pair_evidence += 1
        if ordered_pairs:
            diagnostics.append(
                PhaseDiagnosticsRecord(
                    run_id=run_id,
                    phase_id=phase_id,
                    diagnostic_type="temporal_pairs",
                    result="retained",
                    reason_code="bounded_pair_aggregation",
                    sample_ref=f"pair:{ordered_pairs[0][0]}",
                    details=f"published {emitted_phase_pair_summaries} phase-bounded pair summaries",
                )
            )

    return (
        tuple(phases),
        tuple(phase_central_people),
        tuple(phase_theme_summaries),
        tuple(phase_pair_summaries),
        tuple(phase_pair_evidence),
        tuple(phase_representative_interactions),
        tuple(sorted(diagnostics, key=lambda row: (row.diagnostic_type, row.result, row.phase_id, row.sample_ref))),
        {
            "suppressed_phase_count": suppressed_phase_count,
            "phase_boundary_merged_count": merged_count,
            "phase_boundary_retained_count": retained_count,
            "phase_representative_interaction_cap": MAX_REPRESENTATIVE_INTERACTIONS_PER_PHASE,
            "phase_pair_evidence_cap": MAX_PHASE_PAIR_EVIDENCE_PER_PAIR,
            "phase_pair_evidence_phase_cap": MAX_PHASE_PAIR_EVIDENCE_PER_PHASE,
            "phase_boundary_diagnostic_cap": MAX_BOUNDARY_DIAGNOSTICS,
        },
    )


def run_pipeline(
    bundle: SourceBundle,
    *,
    run_scope: str,
    source_catalog: str = "personal_archive_dev",
) -> PipelineResult:
    run_id = new_run_id()
    started_at = utc_now()
    started_timer = time.perf_counter()

    mentions, person_links, person_suppressed = derive_person_links(bundle.messages, bundle.contacts, run_id)
    candidate_assertions, candidate_summary = derive_candidate_assertions(
        bundle.messages,
        bundle.contacts,
        run_id,
        run_scope,
    )
    candidate_assertions, reviewed_effects, reviewed_links = apply_reviewed_feedback(
        run_id=run_id,
        contacts=bundle.contacts,
        candidate_assertions=candidate_assertions,
        reviewed_assertions=bundle.reviewed_assertions,
        review_assertion_decisions=bundle.review_assertion_decisions,
    )
    link_index = {(link.message_id, link.person_id, link.role): link for link in person_links}
    for link in reviewed_links:
        link_index[(link.message_id, link.person_id, link.role)] = link
    person_links = tuple(link_index.values())
    candidate_summary = _rebuild_candidate_summary(
        candidate_summary,
        candidate_assertions=candidate_assertions,
        reviewed_effects=reviewed_effects,
    )
    theme_tags, theme_suppressed = derive_theme_tags(bundle.messages, run_id)
    search_docs, search_suppressed = build_search_documents(bundle.messages, person_links, theme_tags, run_id)
    person_person_edges, person_person_edge_evidence = build_nlpdata_person_person_outputs(
        person_links,
        run_id=run_id,
        generation_scope=run_scope,
    )

    (
        phases,
        phase_central_people,
        phase_theme_summaries,
        phase_pair_summaries,
        phase_pair_evidence,
        phase_representative_interactions,
        phase_diagnostics,
        phase_metrics,
    ) = _derive_phase_outputs(
        messages=bundle.messages,
        person_links=person_links,
        theme_tags=theme_tags,
        person_person_edges=person_person_edges,
        person_person_edge_evidence=person_person_edge_evidence,
        run_id=run_id,
        generation_scope=run_scope,
    )

    duration_seconds = time.perf_counter() - started_timer
    completed_at = utc_now()
    output_row_counts = {
        "message_mentions": len(mentions),
        "message_person_links": len(person_links),
        "candidate_assertions": len(candidate_assertions),
        "reviewed_effects": len(reviewed_effects),
        "person_person_edges": len(person_person_edges),
        "person_person_edge_evidence": len(person_person_edge_evidence),
        "phases": len(phases),
        "phase_central_people": len(phase_central_people),
        "phase_theme_summaries": len(phase_theme_summaries),
        "phase_pair_summaries": len(phase_pair_summaries),
        "phase_pair_evidence": len(phase_pair_evidence),
        "phase_representative_interactions": len(phase_representative_interactions),
        "phase_diagnostics": len(phase_diagnostics),
        "message_theme_tags": len(theme_tags),
        "message_search_docs": len(search_docs),
    }
    quality_metrics: dict[str, int | float | bool] = {
        **person_suppressed,
        **candidate_summary.suppressed_counts,
        **theme_suppressed,
        **search_suppressed,
        **build_phase_quality_metrics(
            suppressed_phase_count=int(phase_metrics["suppressed_phase_count"]),
            phase_boundary_merged_count=int(phase_metrics["phase_boundary_merged_count"]),
            phase_boundary_retained_count=int(phase_metrics["phase_boundary_retained_count"]),
            phase_representative_interaction_cap=int(phase_metrics["phase_representative_interaction_cap"]),
            phase_pair_evidence_cap=int(phase_metrics["phase_pair_evidence_cap"]),
            phase_pair_evidence_phase_cap=int(phase_metrics["phase_pair_evidence_phase_cap"]),
            phase_boundary_diagnostic_cap=int(phase_metrics["phase_boundary_diagnostic_cap"]),
            phase_diagnostics_count=len(phase_diagnostics),
        ),
        "runtime_seconds": round(duration_seconds, 6),
        "meets_runtime_goal": meets_runtime_goal(len(bundle.messages), duration_seconds),
    }
    run = build_refresh_run(
        run_id=run_id,
        run_scope=run_scope,
        source_catalog=source_catalog,
        started_at=started_at,
        completed_at=completed_at,
        input_interaction_count=len(bundle.messages),
        output_row_counts=output_row_counts,
        quality_metrics=quality_metrics,
    )
    return PipelineResult(
        run=run,
        mentions=mentions,
        person_links=person_links,
        candidate_assertions=candidate_assertions,
        candidate_summary=candidate_summary,
        reviewed_effects=reviewed_effects,
        theme_tags=theme_tags,
        search_docs=search_docs,
        person_person_edges=person_person_edges,
        person_person_edge_evidence=person_person_edge_evidence,
        phases=phases,
        phase_central_people=phase_central_people,
        phase_theme_summaries=phase_theme_summaries,
        phase_pair_summaries=phase_pair_summaries,
        phase_pair_evidence=phase_pair_evidence,
        phase_representative_interactions=phase_representative_interactions,
        phase_diagnostics=phase_diagnostics,
        suppressed_counts={
            key: value
            for key, value in quality_metrics.items()
            if key not in {"runtime_seconds", "meets_runtime_goal"}
        },
    )


def build_pipeline_payload(export_dir: str | Path) -> dict[str, object]:
    bundle = load_source_bundle(export_dir)
    result = run_pipeline(bundle, run_scope=str(export_dir))
    return {
        "nlp_runs": [result.run.to_record()],
        "message_mentions": [row.to_record() for row in result.mentions],
        "message_person_links": [row.to_record() for row in result.person_links],
        "candidate_assertions": [row.to_record() for row in result.candidate_assertions],
        "candidate_assertions_summary": result.candidate_summary.to_record(),
        "reviewed_effects": [row.to_record() for row in result.reviewed_effects],
        "person_person_edges": [row.to_record() for row in result.person_person_edges],
        "person_person_edge_evidence": [row.to_record() for row in result.person_person_edge_evidence],
        "phases": [row.to_record() for row in result.phases],
        "phase_central_people": [row.to_record() for row in result.phase_central_people],
        "phase_theme_summaries": [row.to_record() for row in result.phase_theme_summaries],
        "phase_pair_summaries": [row.to_record() for row in result.phase_pair_summaries],
        "phase_pair_evidence": [row.to_record() for row in result.phase_pair_evidence],
        "phase_representative_interactions": [row.to_record() for row in result.phase_representative_interactions],
        "phase_diagnostics": [row.to_record() for row in result.phase_diagnostics],
        "message_theme_tags": [row.to_record() for row in result.theme_tags],
        "message_search_docs": [row.to_record() for row in result.search_docs],
    }


def write_pipeline_payload(export_dir: str | Path, payload: dict[str, object]) -> Path:
    base = Path(export_dir) / "derived" / "nlpdata"
    base.mkdir(parents=True, exist_ok=True)
    for artifact_name, rows in payload.items():
        if artifact_name == "candidate_assertions_summary":
            path = base / f"{artifact_name}.json"
            with path.open("w", encoding="utf-8") as handle:
                json.dump(rows, handle, indent=2, sort_keys=True)
                handle.write("\n")
            continue

        path = base / f"{artifact_name}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
    return base


def validate_payload_contracts(payload: dict[str, object]) -> None:
    for artifact_name, required_columns in TABLE_CONTRACTS.items():
        rows = payload.get(artifact_name, [])
        if artifact_name == "candidate_assertions_summary":
            if not isinstance(rows, dict):
                raise ValueError(f"{artifact_name} payload must be a dict")
            missing = [column for column in required_columns if column not in rows]
            if missing:
                raise ValueError(f"{artifact_name} payload missing columns: {missing}")
            continue

        if not isinstance(rows, list):
            raise ValueError(f"{artifact_name} payload must be a list of row dicts")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"{artifact_name} row must be a dict")
            missing = [column for column in required_columns if column not in row]
            if missing:
                raise ValueError(f"{artifact_name} row missing columns: {missing}")
