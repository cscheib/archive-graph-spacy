"""Mention extraction for message text."""

from __future__ import annotations

import re
from functools import lru_cache

import spacy

from archive_graph_spacy.models import Mention, Message

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}\d")
NOISE_NAME_SPANS = {
    "hey",
    "hi",
    "hello",
    "team",
    "party",
    "perfect",
    "chat",
    "dinner",
}
GREETING_PREFIXES = ("hi ", "hello ", "hey ")


def _clean_person_candidate(text: str) -> str | None:
    normalized = text.strip()
    lowered = normalized.casefold()
    for prefix in GREETING_PREFIXES:
        if lowered.startswith(prefix):
            normalized = normalized[len(prefix) :].strip()
            lowered = normalized.casefold()
            break
    if not normalized or lowered in NOISE_NAME_SPANS:
        return None
    return normalized


@lru_cache(maxsize=1)
def _load_nlp() -> spacy.language.Language:
    for model_name in ("en_core_web_trf", "en_core_web_lg", "en_core_web_sm"):
        try:
            return spacy.load(model_name, disable=["tagger", "parser", "lemmatizer"])
        except OSError:
            continue
    return spacy.blank("en")


def extract_message_mentions(message: Message) -> list[Mention]:
    """Extract lightweight mentions from subject/body text."""
    nlp = _load_nlp()
    doc = nlp(f"{message.subject}\n{message.body}".strip())

    mentions = [
        Mention(text=match.group(0), label="EMAIL", source="regex")
        for match in EMAIL_PATTERN.finditer(doc.text)
    ]
    mentions.extend(
        Mention(text=match.group(0), label="PHONE", source="regex")
        for match in PHONE_PATTERN.finditer(doc.text)
    )

    if doc.ents:
        mentions.extend(
            Mention(text=cleaned, label=ent.label_, source="spacy")
            for ent in doc.ents
            if (cleaned := _clean_person_candidate(ent.text)) is not None
            if ent.label_ == "PERSON"
        )

    # Fallback multi-token heuristic only; avoid single-token noise like greetings.
    current_name: list[str] = []
    for token in doc:
        if token.text.istitle() and token.is_alpha:
            current_name.append(token.text)
            continue
        if len(current_name) >= 2:
            candidate = _clean_person_candidate(" ".join(current_name))
            if candidate is not None:
                mentions.append(
                    Mention(
                        text=candidate,
                        label="PERSON_CANDIDATE",
                        source="heuristic",
                    )
                )
        current_name = []
    if len(current_name) >= 2:
        candidate = _clean_person_candidate(" ".join(current_name))
        if candidate is not None:
            mentions.append(
                Mention(
                    text=candidate,
                    label="PERSON_CANDIDATE",
                    source="heuristic",
                )
            )

    deduped: list[Mention] = []
    seen = set()
    for mention in mentions:
        key = (mention.text, mention.label, mention.source)
        if key not in seen:
            seen.add(key)
            deduped.append(mention)
    return deduped
