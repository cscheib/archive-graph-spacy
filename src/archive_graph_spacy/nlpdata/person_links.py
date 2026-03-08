"""Canonical person-message link derivation."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import timezone, datetime

from archive_graph_spacy.link.person import link_mentions_to_people
from archive_graph_spacy.models import Contact, Mention, Message

from .mentions import extract_message_mentions
from .models import CandidateAssertion, CandidateDiagnosticsSummary, InteractionMention, PersonMessageLink
from .source_loader import contact_email_index, effective_person_contacts

MIN_PERSON_LINK_CONFIDENCE = 0.5
MIN_RELAY_CANDIDATE_CONFIDENCE = 0.75


def _link_id(message_id: str, person_id: str, role: str, origin: str) -> str:
    digest = hashlib.sha1(f"{message_id}|{person_id}|{role}|{origin}".encode("utf-8")).hexdigest()[:12]
    return f"pl-{digest}"


def _score_reason(reasons: tuple[str, ...]) -> str:
    if "exact_phone" in reasons:
        return "exact_phone_match"
    if "exact_email" in reasons:
        return "exact_email_match"
    if "exact_name" in reasons:
        return "exact_name_match"
    if "name_token" in reasons:
        return "name_token_match"
    return "candidate_match"


def _candidate_id(assertion_type: str, subject_canonical_id: str, proposed_claim: str, generation_scope: str) -> str:
    digest = hashlib.sha1(
        f"{assertion_type}|{subject_canonical_id}|{proposed_claim}|{generation_scope}".encode("utf-8")
    ).hexdigest()[:12]
    return f"ca-{digest}"


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relay_supporting_signal(link: PersonMessageLink) -> bool:
    return (
        link.role == "mentioned"
        and link.link_origin == "inferred"
        and link.confidence >= MIN_RELAY_CANDIDATE_CONFIDENCE
        and link.evidence_type in {"exact_phone_match", "exact_email_match", "exact_name_match"}
    )


def _looks_like_relay_sender(sender: str) -> bool:
    local_part = sender.partition("@")[0].casefold()
    return "+" in local_part or "relay" in local_part


def _matches_leading_name_token(mention_text: str, person_name: str) -> bool:
    parts = person_name.casefold().split()
    return bool(parts) and mention_text.casefold() == parts[0]


def _relay_candidate(
    *,
    run_id: str,
    generation_scope: str,
    message: Message,
    link: PersonMessageLink,
) -> CandidateAssertion:
    proposed_claim = f"relay sender {message.sender} maps to {link.person_id}"
    return CandidateAssertion(
        candidate_assertion_id=_candidate_id("relay_sender_identity", message.message_id, proposed_claim, generation_scope),
        run_id=run_id,
        assertion_type="relay_sender_identity",
        subject_canonical_id=message.message_id,
        proposed_claim=proposed_claim,
        evidence_refs=(
            f"message:{message.message_id}",
            f"sender:{message.sender}",
            f"supporting_signal:{link.evidence_type}:{link.evidence_value}",
        ),
        provenance_summary=f"Derived from unresolved sender plus inferred link from message {message.message_id}",
        confidence_level=link.confidence,
        generation_scope=generation_scope,
        generated_at=_generated_at(),
        review_class="reviewable",
        promotion_class="promotion_eligible",
    )


def _disambiguation_candidate(
    *,
    run_id: str,
    generation_scope: str,
    message: Message,
    mention: InteractionMention,
    candidates: list,
) -> CandidateAssertion:
    plausible_ids = tuple(candidate.person_id for candidate in candidates)
    proposed_claim = f"mention {mention.span_text!r} is ambiguous across {', '.join(plausible_ids)}"
    evidence_refs = [f"message:{message.message_id}", f"mention:{mention.mention_id}"]
    evidence_refs.extend(
        f"candidate_reason:{candidate.person_id}:{'/'.join(candidate.reasons)}"
        for candidate in candidates
    )
    return CandidateAssertion(
        candidate_assertion_id=_candidate_id("person_link_disambiguation", message.message_id, proposed_claim, generation_scope),
        run_id=run_id,
        assertion_type="person_link_disambiguation",
        subject_canonical_id=message.message_id,
        proposed_claim=proposed_claim,
        evidence_refs=tuple(evidence_refs),
        provenance_summary=f"Derived from ambiguous mention-link analysis for message {message.message_id}",
        confidence_level=max(candidate.score for candidate in candidates),
        generation_scope=generation_scope,
        generated_at=_generated_at(),
        review_class="reviewable",
        promotion_class="derived_only",
    )


def _is_reviewable_disambiguation(
    mention: InteractionMention,
    candidates: list,
    person_lookup: dict[str, Contact],
) -> bool:
    if len(mention.span_text.split()) != 1:
        return False
    for candidate in candidates:
        contact = person_lookup.get(candidate.person_id)
        if contact is None or not _matches_leading_name_token(mention.span_text, contact.display_name):
            return False
    return True


def _candidate_summary(
    *,
    run_id: str,
    generation_scope: str,
    candidates: tuple[CandidateAssertion, ...],
    suppressed: dict[str, int],
) -> CandidateDiagnosticsSummary:
    counts: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        counts[candidate.assertion_type] += 1
    return CandidateDiagnosticsSummary(
        run_id=run_id,
        generation_scope=generation_scope,
        emitted_candidate_count=len(candidates),
        candidate_counts_by_type=dict(counts),
        suppressed_counts=dict(suppressed),
        example_candidate_ids=tuple(candidate.candidate_assertion_id for candidate in candidates[:5]),
        generated_at=_generated_at(),
    )


def derive_candidate_assertions(
    messages: tuple[Message, ...],
    contacts: tuple[Contact, ...],
    run_id: str,
    generation_scope: str,
) -> tuple[tuple[CandidateAssertion, ...], CandidateDiagnosticsSummary]:
    candidates_by_id: dict[str, CandidateAssertion] = {}
    suppressed = defaultdict(int)
    email_lookup = contact_email_index(contacts)
    person_contacts = effective_person_contacts(contacts)
    person_lookup = {contact.person_id: contact for contact in person_contacts}

    for message in messages:
        sender_contact = email_lookup.get(message.sender.casefold())
        extracted_mentions = extract_message_mentions(message, run_id)
        mention_candidates = [
            Mention(text=mention.span_text, label=mention.label, source=mention.source_type)
            for mention in extracted_mentions
        ]
        linked = link_mentions_to_people(mention_candidates, list(person_contacts))

        if _looks_like_relay_sender(message.sender) and (sender_contact is None or sender_contact.entity_type != "person"):
            supporting_links: list[PersonMessageLink] = []
            for mention in extracted_mentions:
                linked_candidates = linked.get(mention.span_text, [])
                if not linked_candidates:
                    continue
                best = linked_candidates[0]
                if best.score < MIN_PERSON_LINK_CONFIDENCE:
                    continue
                support_link = PersonMessageLink(
                    link_id=_link_id(message.message_id, best.person_id, "mentioned", "inferred"),
                    run_id=run_id,
                    message_id=message.message_id,
                    person_id=best.person_id,
                    person_name="",
                    role="mentioned",
                    link_origin="inferred",
                    confidence=best.score,
                    evidence_type=_score_reason(best.reasons),
                    evidence_value=mention.span_text,
                    source_interaction_id=message.message_id,
                )
                if _relay_supporting_signal(support_link):
                    supporting_links.append(support_link)
            unique_supporting_ids = {link.person_id for link in supporting_links}
            if len(unique_supporting_ids) == 1 and supporting_links:
                relay_candidate = _relay_candidate(
                    run_id=run_id,
                    generation_scope=generation_scope,
                    message=message,
                    link=supporting_links[0],
                )
                candidates_by_id[relay_candidate.candidate_assertion_id] = relay_candidate
            else:
                suppressed["suppressed_relay_sender_candidate"] += 1

        for mention in extracted_mentions:
            linked_candidates = linked.get(mention.span_text, [])
            if len(linked_candidates) <= 1:
                continue
            best = linked_candidates[0]
            if best.score >= MIN_PERSON_LINK_CONFIDENCE:
                suppressed["suppressed_disambiguation_clear_winner"] += 1
                continue
            if not _is_reviewable_disambiguation(mention, linked_candidates, person_lookup):
                suppressed["suppressed_disambiguation_low_value"] += 1
                continue
            candidate = _disambiguation_candidate(
                run_id=run_id,
                generation_scope=generation_scope,
                message=message,
                mention=mention,
                candidates=linked_candidates,
            )
            candidates_by_id[candidate.candidate_assertion_id] = candidate

    candidates = tuple(candidates_by_id.values())
    return candidates, _candidate_summary(
        run_id=run_id,
        generation_scope=generation_scope,
        candidates=candidates,
        suppressed=dict(suppressed),
    )


def derive_person_links(
    messages: tuple[Message, ...],
    contacts: tuple[Contact, ...],
    run_id: str,
) -> tuple[tuple[InteractionMention, ...], tuple[PersonMessageLink, ...], dict[str, int]]:
    published_mentions: list[InteractionMention] = []
    published_links: dict[tuple[str, str, str], PersonMessageLink] = {}
    suppressed = defaultdict(int)
    email_lookup = contact_email_index(contacts)
    person_contacts = effective_person_contacts(contacts)
    person_lookup = {contact.person_id: contact for contact in person_contacts}

    for message in messages:
        explicit_participants: set[str] = set()
        sender_contact = email_lookup.get(message.sender.casefold())
        if sender_contact is None:
            suppressed["unresolved_sender"] += 1
        elif sender_contact.entity_type != "person":
            suppressed["suppressed_non_person_explicit_link"] += 1
        else:
            explicit_participants.add(sender_contact.person_id)
            link = PersonMessageLink(
                link_id=_link_id(message.message_id, sender_contact.person_id, "sender", "explicit"),
                run_id=run_id,
                message_id=message.message_id,
                person_id=sender_contact.person_id,
                person_name=sender_contact.display_name,
                role="sender",
                link_origin="explicit",
                confidence=1.0,
                evidence_type="header_email",
                evidence_value=message.sender,
                source_interaction_id=message.message_id,
            )
            published_links[(link.message_id, link.person_id, link.role)] = link

        for recipient in message.recipients:
            recipient_contact = email_lookup.get(recipient.casefold())
            if recipient_contact is None:
                suppressed["unresolved_recipient"] += 1
                continue
            if recipient_contact.entity_type != "person":
                suppressed["suppressed_non_person_explicit_link"] += 1
                continue
            explicit_participants.add(recipient_contact.person_id)
            link = PersonMessageLink(
                link_id=_link_id(message.message_id, recipient_contact.person_id, "recipient", "explicit"),
                run_id=run_id,
                message_id=message.message_id,
                person_id=recipient_contact.person_id,
                person_name=recipient_contact.display_name,
                role="recipient",
                link_origin="explicit",
                confidence=1.0,
                evidence_type="header_email",
                evidence_value=recipient,
                source_interaction_id=message.message_id,
            )
            published_links[(link.message_id, link.person_id, link.role)] = link

        extracted_mentions = extract_message_mentions(message, run_id)
        mention_candidates = [
            Mention(text=mention.span_text, label=mention.label, source=mention.source_type)
            for mention in extracted_mentions
        ]
        linked = link_mentions_to_people(
            mention_candidates,
            list(person_contacts),
            preferred_person_ids=explicit_participants,
        )
        for mention in extracted_mentions:
            if mention.span_text not in linked:
                published_mentions.append(mention)
                continue
            candidates = linked[mention.span_text]
            best = candidates[0]
            if best.score < MIN_PERSON_LINK_CONFIDENCE:
                suppressed["suppressed_low_confidence_person_link"] += 1
                published_mentions.append(mention)
                continue
            contact = person_lookup.get(best.person_id)
            if contact is None:
                suppressed["suppressed_non_person_inferred_link"] += 1
                published_mentions.append(mention)
                continue
            link = PersonMessageLink(
                link_id=_link_id(message.message_id, contact.person_id, "mentioned", "inferred"),
                run_id=run_id,
                message_id=message.message_id,
                person_id=contact.person_id,
                person_name=contact.display_name,
                role="mentioned",
                link_origin="inferred",
                confidence=best.score,
                evidence_type=_score_reason(best.reasons),
                evidence_value=mention.span_text,
                source_interaction_id=message.message_id,
            )
            published_links[(link.message_id, link.person_id, link.role)] = link
            published_mentions.append(mention)

    return (
        tuple(published_mentions),
        tuple(published_links.values()),
        dict(suppressed),
    )
