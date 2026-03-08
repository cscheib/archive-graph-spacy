"""Search-document projection for nlpdata."""

from __future__ import annotations

import re

from archive_graph_spacy.models import Message

from .models import PersonMessageLink, SearchDocument, ThemeTag
from .themes import is_system_generated_message


def _tokenize(text: str) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered_tokens: list[str] = []
    for token in re.findall(r"[A-Za-z0-9']+", text.casefold()):
        if len(token) < 3:
            continue
        if token in seen:
            continue
        seen.add(token)
        ordered_tokens.append(token)
    return tuple(ordered_tokens)


def _time_facets(message: Message) -> dict[str, str]:
    if message.timestamp is None:
        return {}
    return {
        "year": f"{message.timestamp.year:04d}",
        "month": f"{message.timestamp.month:02d}",
        "day": f"{message.timestamp.day:02d}",
        "year_month": f"{message.timestamp.year:04d}-{message.timestamp.month:02d}",
    }


def build_search_documents(
    messages: tuple[Message, ...],
    person_links: tuple[PersonMessageLink, ...],
    theme_tags: tuple[ThemeTag, ...],
    run_id: str,
) -> tuple[tuple[SearchDocument, ...], dict[str, int]]:
    links_by_message: dict[str, list[PersonMessageLink]] = {}
    for link in person_links:
        links_by_message.setdefault(link.message_id, []).append(link)

    themes_by_message: dict[str, list[ThemeTag]] = {}
    for tag in theme_tags:
        themes_by_message.setdefault(tag.message_id, []).append(tag)

    documents: list[SearchDocument] = []
    suppressed: dict[str, int] = {
        "suppressed_empty_search_document": 0,
        "suppressed_system_generated_search_document": 0,
        "flagged_unresolved_derivations": 0,
    }

    for message in messages:
        if is_system_generated_message(message):
            suppressed["suppressed_system_generated_search_document"] += 1
            continue

        links = sorted(links_by_message.get(message.message_id, []), key=lambda link: (link.role, link.person_id))
        tags = sorted(themes_by_message.get(message.message_id, []), key=lambda tag: tag.theme)
        if not links and not tags:
            suppressed["suppressed_empty_search_document"] += 1
            continue

        linked_person_ids = tuple(link.person_id for link in links)
        linked_person_names = tuple(link.person_name for link in links)
        explicit_person_ids = tuple(link.person_id for link in links if link.link_origin == "explicit")
        inferred_person_ids = tuple(link.person_id for link in links if link.link_origin == "inferred")
        if not explicit_person_ids and not inferred_person_ids:
            suppressed["flagged_unresolved_derivations"] += 1

        documents.append(
            SearchDocument(
                message_id=message.message_id,
                run_id=run_id,
                source_interaction_id=message.message_id,
                source_type=message.source,
                timestamp=message.timestamp.isoformat() if message.timestamp else None,
                subject_terms=_tokenize(message.subject),
                body_terms=_tokenize(message.body),
                linked_person_ids=linked_person_ids,
                linked_person_names=linked_person_names,
                explicit_person_ids=explicit_person_ids,
                inferred_person_ids=inferred_person_ids,
                theme_labels=tuple(tag.theme for tag in tags),
                time_facets=_time_facets(message),
            )
        )

    return tuple(documents), suppressed


def query_search_documents(
    documents: tuple[SearchDocument, ...],
    *,
    person_id: str | None = None,
    theme: str | None = None,
) -> tuple[SearchDocument, ...]:
    rows = documents
    if person_id is not None:
        rows = tuple(doc for doc in rows if person_id in doc.linked_person_ids)
    if theme is not None:
        rows = tuple(doc for doc in rows if theme in doc.theme_labels)
    return rows
