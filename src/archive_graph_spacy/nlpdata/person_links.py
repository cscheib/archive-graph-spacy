"""Canonical person-message link derivation."""

from __future__ import annotations

import hashlib
from collections import defaultdict

from archive_graph_spacy.link.person import link_mentions_to_people
from archive_graph_spacy.models import Contact, Mention, Message

from .mentions import extract_message_mentions
from .models import InteractionMention, PersonMessageLink
from .source_loader import contact_email_index, effective_person_contacts

MIN_PERSON_LINK_CONFIDENCE = 0.5


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
