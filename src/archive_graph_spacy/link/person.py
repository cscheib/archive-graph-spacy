"""Candidate linking from extracted mentions to contacts."""

from __future__ import annotations

import re

from archive_graph_spacy.models import Contact, LinkCandidate, Mention


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D+", "", value)


def link_mentions_to_people(
    mentions: list[Mention],
    contacts: list[Contact],
    *,
    preferred_person_ids: set[str] | None = None,
) -> dict[str, list[LinkCandidate]]:
    """Return scored person candidates keyed by mention text."""
    results: dict[str, list[LinkCandidate]] = {}
    preferred_ids = preferred_person_ids or set()
    for mention in mentions:
        candidates: list[LinkCandidate] = []
        normalized_text = mention.text.casefold()
        normalized_phone = _normalize_phone(mention.text)
        for contact in contacts:
            reasons: list[str] = []
            score = 0.0

            if (
                mention.label in {"PERSON", "PERSON_CANDIDATE"}
                and normalized_text == contact.display_name.casefold()
            ):
                score += 1.0
                reasons.append("exact_name")
            if normalized_text in {email.casefold() for email in contact.emails}:
                score += 1.0
                reasons.append("exact_email")
            contact_phones = {
                _normalize_phone(phone) for phone in contact.phones if _normalize_phone(phone)
            }
            if mention.label == "PHONE" and normalized_phone and normalized_phone in contact_phones:
                score += 1.0
                reasons.append("exact_phone")
            if (
                mention.label in {"PERSON", "PERSON_CANDIDATE"}
                and len(normalized_text.split()) == 1
                and normalized_text not in {"hey", "hi", "hello", "team"}
                and normalized_text in contact.display_name.casefold().split()
            ):
                score += 0.25
                reasons.append("name_token")

            if score:
                candidates.append(
                    LinkCandidate(
                        person_id=contact.person_id,
                        score=score,
                        reasons=tuple(reasons),
                    )
                )

        if candidates and mention.label in {"PERSON", "PERSON_CANDIDATE"} and len(normalized_text.split()) == 1:
            preferred_candidates = [
                candidate for candidate in candidates if candidate.person_id in preferred_ids
            ]
            if preferred_candidates:
                if len(preferred_candidates) == 1:
                    winner = preferred_candidates[0]
                    bonus = 0.75
                    candidates = [
                        LinkCandidate(
                            person_id=winner.person_id,
                            score=winner.score + bonus,
                            reasons=winner.reasons + ("explicit_participant_context",),
                        )
                    ]
                else:
                    candidates = [
                        LinkCandidate(
                            person_id=candidate.person_id,
                            score=candidate.score + 0.25,
                            reasons=candidate.reasons + ("explicit_participant_context",),
                        )
                        for candidate in preferred_candidates
                    ]

        if candidates:
            results[mention.text] = sorted(
                candidates,
                key=lambda candidate: candidate.score,
                reverse=True,
            )

    return results
