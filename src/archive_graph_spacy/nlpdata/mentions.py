"""Message-level mention derivation with provenance."""

from __future__ import annotations

import hashlib
import re
from functools import lru_cache

import spacy

from archive_graph_spacy.models import Message

from .models import InteractionMention

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}\d")
NOISE_SPANS = {"hey", "hi", "hello", "team", "party", "perfect", "chat", "dinner"}
GREETING_PREFIXES = ("hi ", "hello ", "hey ")


def _normalized_person_text(text: str) -> str | None:
    normalized = text.strip()
    lowered = normalized.casefold()
    for prefix in GREETING_PREFIXES:
        if lowered.startswith(prefix):
            normalized = normalized[len(prefix) :].strip()
            lowered = normalized.casefold()
            break
    if not normalized or lowered in NOISE_SPANS:
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


def _message_text(message: Message) -> str:
    subject = message.subject.strip()
    body = message.body.strip()
    if subject and body:
        return f"{subject}\n{body}"
    return subject or body


def _mention_id(message_id: str, label: str, start_char: int, end_char: int, text: str) -> str:
    digest = hashlib.sha1(
        f"{message_id}|{label}|{start_char}|{end_char}|{text}".encode("utf-8")
    ).hexdigest()[:12]
    return f"mm-{digest}"


def _has_covering_multi_token_person_span(
    mentions: list[InteractionMention],
    start_char: int,
    end_char: int,
) -> bool:
    for mention in mentions:
        if mention.label not in {"PERSON", "PERSON_CANDIDATE"}:
            continue
        if len(mention.span_text.split()) < 2:
            continue
        if mention.start_char <= start_char and mention.end_char >= end_char:
            return True
    return False


def extract_message_mentions(message: Message, run_id: str) -> tuple[InteractionMention, ...]:
    text = _message_text(message)
    if not text:
        return ()

    doc = _load_nlp()(text)
    mentions: list[InteractionMention] = []

    for match in EMAIL_PATTERN.finditer(text):
        mentions.append(
            InteractionMention(
                mention_id=_mention_id(message.message_id, "EMAIL", match.start(), match.end(), match.group(0)),
                run_id=run_id,
                message_id=message.message_id,
                source_interaction_id=message.message_id,
                span_text=match.group(0),
                label="EMAIL",
                start_char=match.start(),
                end_char=match.end(),
                source_type="regex",
                confidence=1.0,
            )
        )

    for match in PHONE_PATTERN.finditer(text):
        mentions.append(
            InteractionMention(
                mention_id=_mention_id(message.message_id, "PHONE", match.start(), match.end(), match.group(0)),
                run_id=run_id,
                message_id=message.message_id,
                source_interaction_id=message.message_id,
                span_text=match.group(0),
                label="PHONE",
                start_char=match.start(),
                end_char=match.end(),
                source_type="regex",
                confidence=1.0,
            )
        )

    for ent in doc.ents:
        if ent.label_ != "PERSON":
            continue
        if (cleaned := _normalized_person_text(ent.text)) is None:
            continue
        mentions.append(
            InteractionMention(
                mention_id=_mention_id(message.message_id, ent.label_, ent.start_char, ent.end_char, cleaned),
                run_id=run_id,
                message_id=message.message_id,
                source_interaction_id=message.message_id,
                span_text=cleaned,
                label="PERSON",
                start_char=ent.start_char,
                end_char=ent.end_char,
                source_type="spacy",
                confidence=0.85,
            )
        )

    current_tokens: list[spacy.tokens.Token] = []
    for token in doc:
        if token.text.istitle() and token.is_alpha:
            current_tokens.append(token)
            continue
        if len(current_tokens) >= 2:
            cleaned = _normalized_person_text(" ".join(token.text for token in current_tokens))
            if cleaned is not None:
                start = current_tokens[0].idx
                end = current_tokens[-1].idx + len(current_tokens[-1].text)
                mentions.append(
                    InteractionMention(
                        mention_id=_mention_id(message.message_id, "PERSON_CANDIDATE", start, end, cleaned),
                        run_id=run_id,
                        message_id=message.message_id,
                        source_interaction_id=message.message_id,
                        span_text=cleaned,
                        label="PERSON_CANDIDATE",
                        start_char=start,
                        end_char=end,
                        source_type="heuristic",
                        confidence=0.55,
                    )
                )
        current_tokens = []
    if len(current_tokens) >= 2:
        cleaned = _normalized_person_text(" ".join(token.text for token in current_tokens))
        if cleaned is not None:
            start = current_tokens[0].idx
            end = current_tokens[-1].idx + len(current_tokens[-1].text)
            mentions.append(
                InteractionMention(
                    mention_id=_mention_id(message.message_id, "PERSON_CANDIDATE", start, end, cleaned),
                    run_id=run_id,
                    message_id=message.message_id,
                    source_interaction_id=message.message_id,
                    span_text=cleaned,
                    label="PERSON_CANDIDATE",
                    start_char=start,
                    end_char=end,
                    source_type="heuristic",
                    confidence=0.55,
                    )
                )

    # Keep low-confidence single-token candidates so downstream suppression rules
    # can account for ambiguous names without publishing them as trusted links.
    for token in doc:
        if not (token.text.istitle() and token.is_alpha):
            continue
        cleaned = _normalized_person_text(token.text)
        if cleaned is None:
            continue
        start_char = token.idx
        end_char = token.idx + len(token.text)
        if _has_covering_multi_token_person_span(mentions, start_char, end_char):
            continue
        mentions.append(
            InteractionMention(
                mention_id=_mention_id(message.message_id, "PERSON_CANDIDATE", start_char, end_char, cleaned),
                run_id=run_id,
                message_id=message.message_id,
                source_interaction_id=message.message_id,
                span_text=cleaned,
                label="PERSON_CANDIDATE",
                start_char=start_char,
                end_char=end_char,
                source_type="heuristic",
                confidence=0.25,
            )
        )

    deduped: dict[tuple[str, str, int, int, str], InteractionMention] = {}
    for mention in mentions:
        key = (
            mention.message_id,
            mention.label,
            mention.start_char,
            mention.end_char,
            mention.span_text,
        )
        deduped[key] = mention
    return tuple(deduped.values())
