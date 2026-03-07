"""Deterministic message-level theme tagging."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict

from archive_graph_spacy.models import Message

from .models import ThemeTag

THEME_RULES: dict[str, tuple[str, ...]] = {
    "family": ("mom", "dad", "family", "kids", "brother", "sister"),
    "work": ("meeting", "project", "client", "deadline", "proposal"),
    "travel": ("flight", "hotel", "trip", "airport", "booking"),
    "support": ("support", "issue", "ticket", "help", "problem"),
}
MIN_THEME_CONFIDENCE = 0.75


def _theme_tag_id(message_id: str, theme: str) -> str:
    digest = hashlib.sha1(f"{message_id}|{theme}".encode("utf-8")).hexdigest()[:12]
    return f"tt-{digest}"


def is_system_generated_message(message: Message) -> bool:
    sender = message.sender.casefold()
    local_part = sender.split("@", 1)[0] if "@" in sender else sender
    if local_part in {"noreply", "no-reply", "notifications", "notification", "support", "info"}:
        return True
    if message.interaction_type and "notification" in message.interaction_type.casefold():
        return True
    if not message.subject.strip() and not message.body.strip():
        return True
    return False


def derive_theme_tags(messages: tuple[Message, ...], run_id: str) -> tuple[tuple[ThemeTag, ...], dict[str, int]]:
    published: list[ThemeTag] = []
    suppressed = defaultdict(int)
    for message in messages:
        if is_system_generated_message(message):
            suppressed["suppressed_system_generated_message"] += 1
            continue
        haystack = f"{message.subject}\n{message.body}".casefold()
        for theme, keywords in THEME_RULES.items():
            evidence_terms: list[str] = []
            match_count = 0
            for keyword in keywords:
                occurrences = re.findall(rf"\b{re.escape(keyword)}\b", haystack)
                if occurrences:
                    evidence_terms.append(keyword)
                    match_count += len(occurrences)
            if not evidence_terms:
                continue
            confidence = min(0.55 + 0.15 * match_count, 0.95)
            if confidence < MIN_THEME_CONFIDENCE:
                suppressed["suppressed_low_confidence_theme"] += 1
                continue
            published.append(
                ThemeTag(
                    theme_tag_id=_theme_tag_id(message.message_id, theme),
                    run_id=run_id,
                    message_id=message.message_id,
                    theme=theme,
                    confidence=confidence,
                    evidence=", ".join(evidence_terms),
                    source_method="rule_based",
                    source_interaction_id=message.message_id,
                )
            )
    return tuple(published), dict(suppressed)
