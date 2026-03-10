"""Canonical person-message link derivation."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import timezone, datetime
from dataclasses import dataclass
from typing import Sequence

from archive_graph_spacy.link.person import link_mentions_to_people
from archive_graph_spacy.models import Contact, LinkCandidate, Mention, Message

from .mentions import extract_message_mentions
from .models import (
    CandidateAssertion,
    CandidateDiagnosticsSummary,
    InteractionMention,
    PersonMessageLink,
    ReviewedEffectResult,
)
from .runs import semantic_replay_key
from .source_loader import _ensure_list, contact_email_index, effective_person_contacts

MIN_PERSON_LINK_CONFIDENCE = 0.5
MIN_RELAY_CANDIDATE_CONFIDENCE = 0.75
RELATIONSHIP_REVIEW_MIN_SCORE = 0.75


@dataclass(frozen=True)
class DerivedLinkContext:
    message: Message
    extracted_mentions: tuple[InteractionMention, ...]
    linked_candidates: dict[str, list[LinkCandidate]]
    explicit_participants: frozenset[str]


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


def _canonical_pair_id(person_a_id: str, person_b_id: str) -> str:
    readable_pair_id = "|".join(sorted((person_a_id, person_b_id)))
    digest = hashlib.sha1(readable_pair_id.encode("utf-8")).hexdigest()[:12]
    return f"pair-{digest}"


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


def _explicit_participants(
    message: Message,
    email_lookup: dict[str, Contact],
) -> set[str]:
    explicit_participants: set[str] = set()
    sender_contact = email_lookup.get(message.sender.casefold())
    if sender_contact is not None and sender_contact.entity_type == "person":
        explicit_participants.add(sender_contact.person_id)
    for recipient in message.recipients:
        recipient_contact = email_lookup.get(recipient.casefold())
        if recipient_contact is not None and recipient_contact.entity_type == "person":
            explicit_participants.add(recipient_contact.person_id)
    return explicit_participants


def derive_link_contexts(
    messages: tuple[Message, ...],
    contacts: tuple[Contact, ...],
    run_id: str,
) -> tuple[DerivedLinkContext, ...]:
    email_lookup = contact_email_index(contacts)
    person_contacts = effective_person_contacts(contacts)
    contexts: list[DerivedLinkContext] = []
    for message in messages:
        explicit_participants = _explicit_participants(message, email_lookup)
        extracted_mentions = extract_message_mentions(message, run_id)
        mention_candidates = [
            Mention(text=mention.span_text, label=mention.label, source=mention.source_type)
            for mention in extracted_mentions
        ]
        linked_candidates = link_mentions_to_people(
            mention_candidates,
            list(person_contacts),
            preferred_person_ids=explicit_participants,
        )
        contexts.append(
            DerivedLinkContext(
                message=message,
                extracted_mentions=extracted_mentions,
                linked_candidates=linked_candidates,
                explicit_participants=frozenset(explicit_participants),
            )
        )
    return tuple(contexts)


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
    candidates: Sequence[LinkCandidate],
) -> CandidateAssertion:
    plausible_ids = tuple(candidate.person_id for candidate in candidates)
    proposed_claim = f"mention {mention.mention_id} {mention.span_text!r} is ambiguous across {', '.join(plausible_ids)}"
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


def _relationship_evidence_candidate(
    *,
    run_id: str,
    generation_scope: str,
    person_a_id: str,
    person_b_id: str,
    direct_count: int,
    indirect_count: int,
    evidence_refs: tuple[str, ...],
) -> CandidateAssertion:
    readable_pair_id = "|".join(sorted((person_a_id, person_b_id)))
    pair_canonical_id = _canonical_pair_id(person_a_id, person_b_id)
    proposed_claim = (
        f"pair {readable_pair_id} has conflicting relationship evidence "
        f"(direct={direct_count}, indirect={indirect_count})"
    )
    return CandidateAssertion(
        candidate_assertion_id=_candidate_id(
            "relationship_evidence_review",
            pair_canonical_id,
            proposed_claim,
            generation_scope,
        ),
        run_id=run_id,
        assertion_type="relationship_evidence_review",
        subject_canonical_id=pair_canonical_id,
        proposed_claim=proposed_claim,
        evidence_refs=evidence_refs + (f"pair_id:{pair_canonical_id}",),
        provenance_summary=(
            "Derived from mixed direct and indirect pair evidence across the bounded run"
        ),
        confidence_level=RELATIONSHIP_REVIEW_MIN_SCORE,
        generation_scope=generation_scope,
        generated_at=_generated_at(),
        review_class="reviewable",
        promotion_class="derived_only",
    )


def _is_reviewable_disambiguation(
    mention: InteractionMention,
    candidates: Sequence[LinkCandidate],
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
    reviewed_effects: tuple[ReviewedEffectResult, ...] = (),
) -> CandidateDiagnosticsSummary:
    counts: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        counts[candidate.assertion_type] += 1
    reviewed_counts: dict[str, int] = defaultdict(int)
    for effect in reviewed_effects:
        reviewed_counts[effect.result] += 1
    return CandidateDiagnosticsSummary(
        run_id=run_id,
        generation_scope=generation_scope,
        emitted_candidate_count=len(candidates),
        candidate_counts_by_type=dict(counts),
        suppressed_counts=dict(suppressed),
        example_candidate_ids=tuple(candidate.candidate_assertion_id for candidate in candidates[:5]),
        generated_at=_generated_at(),
        reviewed_effect_counts=dict(reviewed_counts),
    )


def derive_candidate_assertions(
    messages: tuple[Message, ...],
    contacts: tuple[Contact, ...],
    run_id: str,
    generation_scope: str,
) -> tuple[tuple[CandidateAssertion, ...], CandidateDiagnosticsSummary]:
    candidates_by_id: dict[str, CandidateAssertion] = {}
    suppressed = defaultdict(int)
    contexts = derive_link_contexts(messages, contacts, run_id)
    email_lookup = contact_email_index(contacts)
    person_contacts = effective_person_contacts(contacts)
    person_lookup = {contact.person_id: contact for contact in person_contacts}

    for context in contexts:
        message = context.message
        sender_contact = email_lookup.get(message.sender.casefold())
        extracted_mentions = context.extracted_mentions
        linked = context.linked_candidates

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

    pair_evidence: dict[tuple[str, str], dict[str, object]] = {}
    for context in contexts:
        direct_participants = set(context.explicit_participants)
        sorted_participants = sorted(direct_participants)
        for idx, left in enumerate(sorted_participants):
            for right in sorted_participants[idx + 1 :]:
                pair_key = tuple(sorted((left, right)))
                record = pair_evidence.setdefault(
                    pair_key,
                    {"direct": set(), "indirect": set()},
                )
                record["direct"].add(context.message.message_id)
        for mention in context.extracted_mentions:
            linked_candidates = context.linked_candidates.get(mention.span_text, [])
            if not linked_candidates:
                continue
            best = linked_candidates[0]
            if best.score < MIN_PERSON_LINK_CONFIDENCE:
                continue
            for explicit_person_id in context.explicit_participants:
                if explicit_person_id == best.person_id:
                    continue
                pair_key = tuple(sorted((explicit_person_id, best.person_id)))
                record = pair_evidence.setdefault(
                    pair_key,
                    {"direct": set(), "indirect": set()},
                )
                record["indirect"].add(context.message.message_id)

    for (person_a_id, person_b_id), evidence in pair_evidence.items():
        direct_messages = tuple(sorted(evidence["direct"]))
        indirect_messages = tuple(sorted(evidence["indirect"]))
        if not direct_messages or not indirect_messages:
            continue
        evidence_refs = tuple(
            [f"pair:{person_a_id}|{person_b_id}"]
            + [f"direct_message:{message_id}" for message_id in direct_messages[:3]]
            + [f"indirect_message:{message_id}" for message_id in indirect_messages[:3]]
        )
        candidate = _relationship_evidence_candidate(
            run_id=run_id,
            generation_scope=generation_scope,
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            direct_count=len(direct_messages),
            indirect_count=len(indirect_messages),
            evidence_refs=evidence_refs,
        )
        candidates_by_id[candidate.candidate_assertion_id] = candidate

    candidates = tuple(candidates_by_id.values())
    return candidates, _candidate_summary(
        run_id=run_id,
        generation_scope=generation_scope,
        candidates=candidates,
        suppressed=dict(suppressed),
    )


def _normalized_reviewed_inputs(
    reviewed_assertions: tuple[dict[str, object], ...],
    review_assertion_decisions: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    by_candidate: dict[str, dict[str, object]] = {}
    for row in reviewed_assertions:
        candidate_id = str(row.get("candidate_assertion_id") or "")
        if not candidate_id:
            continue
        by_candidate[candidate_id] = {
            "candidate_assertion_id": candidate_id,
            "assertion_type": str(row.get("assertion_type") or ""),
            "subject_canonical_id": str(row.get("subject_canonical_id") or ""),
            "proposed_claim": str(row.get("proposed_claim") or ""),
            "review_state": str(row.get("current_review_state") or ""),
            "generation_scope": None if row.get("generation_scope") in (None, "") else str(row.get("generation_scope")),
            "evidence_refs": _ensure_list(row.get("evidence_refs")),
        }
    for row in review_assertion_decisions:
        candidate_id = str(row.get("candidate_assertion_id") or "")
        if not candidate_id:
            continue
        if candidate_id in by_candidate:
            by_candidate[candidate_id]["decision_state"] = str(row.get("decision_state") or "")
            continue
        snapshot = row.get("evidence_snapshot")
        parsed: dict[str, object] = {}
        if isinstance(snapshot, str) and snapshot.strip():
            try:
                maybe = json.loads(snapshot)
            except json.JSONDecodeError:
                maybe = {}
            if isinstance(maybe, dict):
                parsed = maybe
        by_candidate[candidate_id] = {
            "candidate_assertion_id": candidate_id,
            "assertion_type": str(parsed.get("assertion_type") or ""),
            "subject_canonical_id": str(parsed.get("subject_canonical_id") or ""),
            "proposed_claim": str(parsed.get("proposed_claim") or ""),
            "review_state": str(row.get("decision_state") or ""),
            "generation_scope": None if parsed.get("generation_scope") in (None, "") else str(parsed.get("generation_scope")),
            "evidence_refs": (),
        }
    return list(by_candidate.values())


def _semantic_key_from_values(
    assertion_type: str,
    subject_canonical_id: str,
    proposed_claim: str,
    generation_scope: str | None = None,
) -> str:
    return semantic_replay_key(
        assertion_type=assertion_type,
        subject_canonical_id=subject_canonical_id,
        proposed_claim=proposed_claim,
        generation_scope=generation_scope,
    )


def _candidate_semantic_key(candidate: CandidateAssertion) -> str:
    return _semantic_key_from_values(
        candidate.assertion_type,
        candidate.subject_canonical_id,
        candidate.proposed_claim,
        candidate.generation_scope,
    )


def _candidate_legacy_semantic_key(candidate: CandidateAssertion) -> str:
    return _semantic_key_from_values(
        candidate.assertion_type,
        candidate.subject_canonical_id,
        candidate.proposed_claim,
    )


def _reviewed_semantic_key(reviewed: dict[str, object]) -> str:
    return _semantic_key_from_values(
        str(reviewed.get("assertion_type") or ""),
        str(reviewed.get("subject_canonical_id") or ""),
        str(reviewed.get("proposed_claim") or ""),
        str(reviewed.get("generation_scope") or "") or None,
    )


def _reviewed_relay_link(
    *,
    reviewed: dict[str, object],
    run_id: str,
    contacts: tuple[Contact, ...],
) -> PersonMessageLink | None:
    proposed_claim = str(reviewed.get("proposed_claim") or "")
    if " maps to " not in proposed_claim:
        return None
    person_id = proposed_claim.rsplit(" maps to ", 1)[-1].strip()
    contact_lookup = {contact.person_id: contact for contact in effective_person_contacts(contacts)}
    contact = contact_lookup.get(person_id)
    if contact is None:
        return None
    message_id = str(reviewed.get("subject_canonical_id") or "")
    sender = proposed_claim.split("relay sender ", 1)[-1].split(" maps to ", 1)[0].strip()
    return PersonMessageLink(
        link_id=_link_id(message_id, person_id, "sender", "reviewed"),
        run_id=run_id,
        message_id=message_id,
        person_id=person_id,
        person_name=contact.display_name,
        role="sender",
        link_origin="reviewed",
        confidence=1.0,
        evidence_type="reviewed_assertion",
        evidence_value=sender,
        source_interaction_id=message_id,
    )


def apply_reviewed_feedback(
    *,
    run_id: str,
    contacts: tuple[Contact, ...],
    candidate_assertions: tuple[CandidateAssertion, ...],
    reviewed_assertions: tuple[dict[str, object], ...],
    review_assertion_decisions: tuple[dict[str, object], ...],
) -> tuple[tuple[CandidateAssertion, ...], tuple[ReviewedEffectResult, ...], tuple[PersonMessageLink, ...]]:
    reviewed_inputs = _normalized_reviewed_inputs(reviewed_assertions, review_assertion_decisions)
    by_candidate_id = {candidate.candidate_assertion_id: candidate for candidate in candidate_assertions}
    by_semantic_key = {
        _candidate_semantic_key(candidate): candidate for candidate in candidate_assertions
    }
    by_legacy_semantic_key = {
        _candidate_legacy_semantic_key(candidate): candidate for candidate in candidate_assertions
    }
    by_subject_family: dict[tuple[str, str], list[CandidateAssertion]] = defaultdict(list)
    for candidate in candidate_assertions:
        by_subject_family[(candidate.assertion_type, candidate.subject_canonical_id)].append(candidate)

    remaining: dict[str, CandidateAssertion] = dict(by_candidate_id)
    reviewed_effects: list[ReviewedEffectResult] = []
    extra_links: dict[tuple[str, str, str], PersonMessageLink] = {}

    for reviewed in reviewed_inputs:
        candidate_id = str(reviewed.get("candidate_assertion_id") or "")
        assertion_type = str(reviewed.get("assertion_type") or "")
        subject_canonical_id = str(reviewed.get("subject_canonical_id") or "")
        review_state = str(reviewed.get("decision_state") or reviewed.get("review_state") or "")
        matched = by_candidate_id.get(candidate_id)
        reviewed_key = _reviewed_semantic_key(reviewed)
        if matched is None:
            matched = by_semantic_key.get(reviewed_key)
        if matched is None and not reviewed.get("generation_scope"):
            matched = by_legacy_semantic_key.get(
                _semantic_key_from_values(
                    assertion_type,
                    subject_canonical_id,
                    str(reviewed.get("proposed_claim") or ""),
                )
            )
        if matched is None:
            possible_conflicts = by_subject_family.get((assertion_type, subject_canonical_id), [])
            if possible_conflicts and review_state == "accepted":
                reviewed_effects.append(
                    ReviewedEffectResult(
                        run_id=run_id,
                        candidate_assertion_id=candidate_id,
                        assertion_type=assertion_type,
                        subject_canonical_id=subject_canonical_id,
                        result="conflicted",
                        reason_code="semantic_mismatch",
                        details="accepted reviewed outcome no longer matches regenerated claim",
                    )
                )
            else:
                reviewed_effects.append(
                    ReviewedEffectResult(
                        run_id=run_id,
                        candidate_assertion_id=candidate_id,
                        assertion_type=assertion_type,
                        subject_canonical_id=subject_canonical_id,
                        result="ignored",
                        reason_code="no_replay_match",
                        details="reviewed input did not match any regenerated candidate",
                    )
                )
            continue

        remaining.pop(matched.candidate_assertion_id, None)
        if review_state == "accepted":
            candidate_matches_review = _candidate_semantic_key(matched) == reviewed_key
            legacy_candidate_matches_review = (
                not reviewed.get("generation_scope")
                and _candidate_legacy_semantic_key(matched)
                == _semantic_key_from_values(
                    assertion_type,
                    subject_canonical_id,
                    str(reviewed.get("proposed_claim") or ""),
                )
            )
            if not (candidate_matches_review or legacy_candidate_matches_review):
                reviewed_effects.append(
                    ReviewedEffectResult(
                        run_id=run_id,
                        candidate_assertion_id=matched.candidate_assertion_id,
                        assertion_type=matched.assertion_type,
                        subject_canonical_id=matched.subject_canonical_id,
                        result="conflicted",
                        reason_code="semantic_mismatch",
                        details="accepted reviewed outcome matched by candidate id but conflicts with regenerated semantics",
                    )
                )
                continue
            link = None
            if matched.assertion_type == "relay_sender_identity":
                link = _reviewed_relay_link(reviewed=reviewed, run_id=run_id, contacts=contacts)
            if link is not None:
                extra_links[(link.message_id, link.person_id, link.role)] = link
            reviewed_effects.append(
                ReviewedEffectResult(
                    run_id=run_id,
                    candidate_assertion_id=matched.candidate_assertion_id,
                    assertion_type=matched.assertion_type,
                    subject_canonical_id=matched.subject_canonical_id,
                    result="applied",
                    reason_code="accepted_review",
                    details="accepted reviewed input applied downstream effect and suppressed candidate re-emission",
                )
            )
        elif review_state in {"rejected", "superseded"}:
            reviewed_effects.append(
                ReviewedEffectResult(
                    run_id=run_id,
                    candidate_assertion_id=matched.candidate_assertion_id,
                    assertion_type=matched.assertion_type,
                    subject_canonical_id=matched.subject_canonical_id,
                    result="suppressed",
                    reason_code=review_state,
                    details="reviewed decision suppressed candidate re-emission",
                )
            )
        else:
            remaining[matched.candidate_assertion_id] = matched
            reviewed_effects.append(
                ReviewedEffectResult(
                    run_id=run_id,
                    candidate_assertion_id=matched.candidate_assertion_id,
                    assertion_type=matched.assertion_type,
                    subject_canonical_id=matched.subject_canonical_id,
                    result="skipped",
                    reason_code="non_terminal_review_state",
                    details="reviewed input is not in an applied or suppressed state",
                )
            )

    return (
        tuple(sorted(remaining.values(), key=lambda candidate: candidate.candidate_assertion_id)),
        tuple(
            sorted(
                reviewed_effects,
                key=lambda effect: (
                    effect.result,
                    effect.assertion_type,
                    effect.subject_canonical_id,
                    effect.candidate_assertion_id,
                ),
            )
        ),
        tuple(sorted(extra_links.values(), key=lambda link: (link.message_id, link.person_id, link.role))),
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
    contexts = derive_link_contexts(messages, contacts, run_id)

    for context in contexts:
        message = context.message
        explicit_participants = set(context.explicit_participants)
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

        for mention in context.extracted_mentions:
            linked = context.linked_candidates
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
