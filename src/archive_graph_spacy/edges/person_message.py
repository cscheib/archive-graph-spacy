"""Build person-message edge rows from message metadata and mention linking."""

from __future__ import annotations

import hashlib
from collections import defaultdict

from archive_graph_spacy.extract import extract_message_mentions
from archive_graph_spacy.link import link_mentions_to_people
from archive_graph_spacy.models import (
    Contact,
    Message,
    PersonMessageEdge,
    PersonMessageEdgeEvidence,
)


def _normalize_email(value: str) -> str:
    return value.strip().casefold()


def _edge_id(
    message_id: str,
    person_id: str,
    role: str,
    *parts: str,
) -> str:
    payload = "|".join([message_id, person_id, role, *parts])
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()
    return f"edge-{digest[:12]}"


def build_person_message_edge_evidence(
    message: Message,
    contacts: list[Contact],
) -> list[PersonMessageEdgeEvidence]:
    """Generate explicit and inferred person-message edge evidence for one message."""
    contact_by_email = {
        _normalize_email(email): contact
        for contact in contacts
        for email in contact.emails
    }
    edges: list[PersonMessageEdgeEvidence] = []
    explicit_participant_ids: set[str] = set()

    sender = _normalize_email(message.sender)
    if sender and sender in contact_by_email:
        contact = contact_by_email[sender]
        explicit_participant_ids.add(contact.person_id)
        edges.append(
            PersonMessageEdgeEvidence(
                edge_id=_edge_id(
                    message.message_id,
                    contact.person_id,
                    "sender",
                    "header_email",
                    message.sender,
                ),
                person_id=contact.person_id,
                message_id=message.message_id,
                role="sender",
                evidence_type="header_email",
                evidence_value=message.sender,
                confidence=1.0,
                source=message.source,
            )
        )

    for recipient in message.recipients:
        normalized = _normalize_email(recipient)
        if normalized and normalized in contact_by_email:
            contact = contact_by_email[normalized]
            explicit_participant_ids.add(contact.person_id)
            edges.append(
                PersonMessageEdgeEvidence(
                    edge_id=_edge_id(
                        message.message_id,
                        contact.person_id,
                        "recipient",
                        "header_email",
                        recipient,
                    ),
                    person_id=contact.person_id,
                    message_id=message.message_id,
                    role="recipient",
                    evidence_type="header_email",
                    evidence_value=recipient,
                    confidence=1.0,
                    source=message.source,
                )
            )

    mentions = extract_message_mentions(message)
    linked = link_mentions_to_people(
        mentions,
        contacts,
        preferred_person_ids=explicit_participant_ids,
    )
    for mention_text, candidates in linked.items():
        for candidate in candidates:
            evidence_type = _reason_to_evidence_type(candidate.reasons[0] if candidate.reasons else "")
            edges.append(
                PersonMessageEdgeEvidence(
                    edge_id=_edge_id(
                        message.message_id,
                        candidate.person_id,
                        "mentioned",
                        evidence_type,
                        mention_text,
                    ),
                    person_id=candidate.person_id,
                    message_id=message.message_id,
                    role="mentioned",
                    evidence_type=evidence_type,
                    evidence_value=mention_text,
                    confidence=candidate.score,
                    source=message.source,
                )
            )

    deduped: list[PersonMessageEdgeEvidence] = []
    seen = set()
    for edge in edges:
        key = (edge.person_id, edge.message_id, edge.role, edge.evidence_type, edge.evidence_value)
        if key not in seen:
            seen.add(key)
            deduped.append(edge)
    return deduped


def aggregate_person_message_edges(
    evidence_rows: list[PersonMessageEdgeEvidence],
) -> list[PersonMessageEdge]:
    grouped: dict[tuple[str, str, str], list[PersonMessageEdgeEvidence]] = defaultdict(list)
    for row in evidence_rows:
        grouped[(row.person_id, row.message_id, row.role)].append(row)

    aggregated: list[PersonMessageEdge] = []
    for (person_id, message_id, role), rows in grouped.items():
        strongest = max(rows, key=lambda row: (row.confidence, row.evidence_type, row.evidence_value))
        aggregated.append(
            PersonMessageEdge(
                edge_id=_edge_id(message_id, person_id, role, "aggregate"),
                person_id=person_id,
                message_id=message_id,
                role=role,
                confidence=max(row.confidence for row in rows),
                source=strongest.source,
                strongest_evidence_type=strongest.evidence_type,
                strongest_evidence_value=strongest.evidence_value,
                evidence_count=len(rows),
            )
        )

    return sorted(
        aggregated,
        key=lambda row: (row.message_id, row.person_id, row.role),
    )


def build_person_message_edges(
    message: Message,
    contacts: list[Contact],
) -> list[PersonMessageEdge]:
    return aggregate_person_message_edges(build_person_message_edge_evidence(message, contacts))


def _reason_to_evidence_type(reason: str) -> str:
    mapping = {
        "exact_name": "exact_name_match",
        "exact_email": "exact_email_match",
        "exact_phone": "exact_phone_match",
        "name_token": "name_token_match",
    }
    return mapping.get(reason, "linked_mention")
