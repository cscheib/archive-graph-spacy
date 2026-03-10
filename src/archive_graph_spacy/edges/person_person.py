"""Project person-person edges from person-message edges."""

from __future__ import annotations

import hashlib
from collections import defaultdict

from archive_graph_spacy.models import (
    PersonMessageEdge,
    PersonPersonEdge,
    PersonPersonEdgeEvidence,
)
from archive_graph_spacy.nlpdata.models import PersonMessageLink, PersonPersonEdgeEvidenceRecord, PersonPersonEdgeRecord


def _pair_ids(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _edge_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()
    return f"pp-{digest[:12]}"


def build_person_person_edge_evidence(
    person_message_edges: list[PersonMessageEdge],
) -> list[PersonPersonEdgeEvidence]:
    """Project person-person evidence rows from aggregated person-message edges."""
    by_message: dict[str, list[PersonMessageEdge]] = defaultdict(list)
    for edge in person_message_edges:
        by_message[edge.message_id].append(edge)

    evidence_rows: list[PersonPersonEdgeEvidence] = []
    for message_id, edges in by_message.items():
        explicit = [edge for edge in edges if edge.role in {"sender", "recipient"}]
        mentioned = [edge for edge in edges if edge.role == "mentioned"]

        # People explicitly on the same message are co-participants.
        for idx, left in enumerate(explicit):
            for right in explicit[idx + 1 :]:
                if left.person_id == right.person_id:
                    continue
                person_a_id, person_b_id = _pair_ids(left.person_id, right.person_id)
                evidence_rows.append(
                    PersonPersonEdgeEvidence(
                        edge_id=_edge_id(
                            message_id,
                            person_a_id,
                            person_b_id,
                            "co_participant",
                        ),
                        person_a_id=person_a_id,
                        person_b_id=person_b_id,
                        message_id=message_id,
                        relationship_type="co_participant",
                        confidence=min(left.confidence, right.confidence),
                        source=left.source,
                    )
                )

        # Explicit participants mentioning another known person create mention edges.
        for explicit_edge in explicit:
            for mentioned_edge in mentioned:
                if explicit_edge.person_id == mentioned_edge.person_id:
                    continue
                person_a_id, person_b_id = _pair_ids(explicit_edge.person_id, mentioned_edge.person_id)
                evidence_rows.append(
                    PersonPersonEdgeEvidence(
                        edge_id=_edge_id(
                            message_id,
                            person_a_id,
                            person_b_id,
                            "message_mention",
                        ),
                        person_a_id=person_a_id,
                        person_b_id=person_b_id,
                        message_id=message_id,
                        relationship_type="message_mention",
                        confidence=min(explicit_edge.confidence, mentioned_edge.confidence),
                        source=explicit_edge.source,
                    )
                )

    deduped: list[PersonPersonEdgeEvidence] = []
    seen = set()
    for row in evidence_rows:
        key = (
            row.person_a_id,
            row.person_b_id,
            row.message_id,
            row.relationship_type,
        )
        if key not in seen:
            seen.add(key)
            deduped.append(row)
    return deduped


def aggregate_person_person_edges(
    evidence_rows: list[PersonPersonEdgeEvidence],
) -> list[PersonPersonEdge]:
    grouped: dict[tuple[str, str], list[PersonPersonEdgeEvidence]] = defaultdict(list)
    for row in evidence_rows:
        grouped[(row.person_a_id, row.person_b_id)].append(row)

    aggregated: list[PersonPersonEdge] = []
    for (person_a_id, person_b_id), rows in grouped.items():
        strongest = max(rows, key=lambda row: (row.confidence, row.relationship_type, row.message_id))
        aggregated.append(
            PersonPersonEdge(
                edge_id=_edge_id(person_a_id, person_b_id, "aggregate"),
                person_a_id=person_a_id,
                person_b_id=person_b_id,
                confidence=max(row.confidence for row in rows),
                message_count=len({row.message_id for row in rows}),
                co_participant_count=sum(
                    1 for row in rows if row.relationship_type == "co_participant"
                ),
                mention_count=sum(
                    1 for row in rows if row.relationship_type == "message_mention"
                ),
                strongest_relationship_type=strongest.relationship_type,
                strongest_message_id=strongest.message_id,
            )
        )

    return sorted(aggregated, key=lambda row: (row.person_a_id, row.person_b_id))


def _pair_id(person_a_id: str, person_b_id: str) -> str:
    digest = hashlib.sha1(f"{person_a_id}|{person_b_id}".encode("utf-8")).hexdigest()[:12]
    return f"pair-{digest}"


def build_nlpdata_person_person_outputs(
    person_links: tuple[PersonMessageLink, ...],
    *,
    run_id: str,
    generation_scope: str,
) -> tuple[tuple[PersonPersonEdgeRecord, ...], tuple[PersonPersonEdgeEvidenceRecord, ...]]:
    by_message: dict[str, list[PersonMessageLink]] = defaultdict(list)
    for link in person_links:
        by_message[link.message_id].append(link)

    evidence_rows: dict[tuple[str, str, str], PersonPersonEdgeEvidenceRecord] = {}
    pair_people: dict[str, tuple[str, str]] = {}
    for message_id, links in by_message.items():
        explicit = [link for link in links if link.role in {"sender", "recipient"}]
        mentioned = [link for link in links if link.role == "mentioned"]

        for idx, left in enumerate(explicit):
            for right in explicit[idx + 1 :]:
                if left.person_id == right.person_id:
                    continue
                person_a_id, person_b_id = _pair_ids(left.person_id, right.person_id)
                pair_id = _pair_id(person_a_id, person_b_id)
                pair_people[pair_id] = (person_a_id, person_b_id)
                row = PersonPersonEdgeEvidenceRecord(
                    pair_evidence_id=_edge_id(message_id, person_a_id, person_b_id, "direct_participation"),
                    pair_id=pair_id,
                    evidence_family="direct_participation",
                    source_ref=f"message:{message_id}",
                    contribution_score=min(left.confidence, right.confidence),
                    rank_within_pair=0,
                    message_ref=message_id,
                    provenance=f"explicit participants on {message_id}",
                )
                evidence_rows[(pair_id, message_id, row.evidence_family)] = row

        for explicit_link in explicit:
            for mentioned_link in mentioned:
                if explicit_link.person_id == mentioned_link.person_id:
                    continue
                person_a_id, person_b_id = _pair_ids(explicit_link.person_id, mentioned_link.person_id)
                pair_id = _pair_id(person_a_id, person_b_id)
                pair_people[pair_id] = (person_a_id, person_b_id)
                row = PersonPersonEdgeEvidenceRecord(
                    pair_evidence_id=_edge_id(message_id, person_a_id, person_b_id, "message_mention"),
                    pair_id=pair_id,
                    evidence_family="message_mention",
                    source_ref=f"message:{message_id}",
                    contribution_score=min(explicit_link.confidence, mentioned_link.confidence),
                    rank_within_pair=0,
                    message_ref=message_id,
                    provenance=f"explicit participant mentioned another person on {message_id}",
                )
                evidence_rows[(pair_id, message_id, row.evidence_family)] = row

    ordered_evidence = sorted(
        evidence_rows.values(),
        key=lambda row: (row.pair_id, -row.contribution_score, row.message_ref, row.evidence_family),
    )
    ranked_evidence: list[PersonPersonEdgeEvidenceRecord] = []
    rank_by_pair: dict[str, int] = defaultdict(int)
    for row in ordered_evidence:
        rank_by_pair[row.pair_id] += 1
        ranked_evidence.append(
            PersonPersonEdgeEvidenceRecord(
                pair_evidence_id=row.pair_evidence_id,
                pair_id=row.pair_id,
                evidence_family=row.evidence_family,
                source_ref=row.source_ref,
                contribution_score=row.contribution_score,
                rank_within_pair=rank_by_pair[row.pair_id],
                message_ref=row.message_ref,
                theme_refs=row.theme_refs,
                provenance=row.provenance,
            )
        )

    grouped: dict[str, list[PersonPersonEdgeEvidenceRecord]] = defaultdict(list)
    for row in ranked_evidence:
        grouped[row.pair_id].append(row)

    summaries: list[PersonPersonEdgeRecord] = []
    for pair_id, rows in grouped.items():
        person_a_id, person_b_id = pair_people[pair_id]
        strongest = max(rows, key=lambda row: (row.contribution_score, -row.rank_within_pair))
        direct_count = sum(1 for row in rows if row.evidence_family == "direct_participation")
        indirect_count = sum(1 for row in rows if row.evidence_family != "direct_participation")
        summaries.append(
            PersonPersonEdgeRecord(
                pair_id=pair_id,
                person_a_id=person_a_id,
                person_b_id=person_b_id,
                run_id=run_id,
                generation_scope=generation_scope,
                strength_score=max(row.contribution_score for row in rows),
                relationship_signal=strongest.evidence_family,
                direct_evidence_count=direct_count,
                indirect_evidence_count=indirect_count,
                strongest_evidence_ref=strongest.source_ref,
                is_current=True,
            )
        )

    return (
        tuple(sorted(summaries, key=lambda row: (row.person_a_id, row.person_b_id))),
        tuple(ranked_evidence),
    )
