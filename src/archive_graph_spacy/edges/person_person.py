"""Project person-person edges from person-message edges."""

from __future__ import annotations

import hashlib
from collections import defaultdict

from archive_graph_spacy.models import (
    PersonMessageEdge,
    PersonPersonEdge,
    PersonPersonEdgeEvidence,
)


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
