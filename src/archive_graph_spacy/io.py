"""Helpers for loading small experiment exports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from archive_graph_spacy.models import Contact, Message


def _read_jsonl(path: str | Path) -> list[dict]:
    with Path(path).open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _coerce_string_array(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(_coerce_string_array(list(value)))
    if isinstance(value, list):
        if len(value) == 1 and isinstance(value[0], str):
            raw = value[0].strip()
            if raw.startswith("[") and raw.endswith("]"):
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return tuple(str(item) for item in parsed if str(item).strip())
        return tuple(str(item) for item in value if str(item).strip())
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return tuple(str(item) for item in parsed if str(item).strip())
        return (raw,) if raw else ()
    return (str(value),)


def load_contacts(path: str | Path) -> list[Contact]:
    return [
        Contact(
            person_id=item["person_id"],
            display_name=item["display_name"],
            emails=_coerce_string_array(item.get("emails", [])),
            phones=_coerce_string_array(item.get("phones", [])),
            photo_url=item.get("photo_url"),
            entity_type=item.get("entity_type") or "unknown",
        )
        for item in _read_jsonl(path)
    ]


def load_messages(path: str | Path) -> list[Message]:
    return [
        Message(
            message_id=item["message_id"],
            source=item["source"],
            sender=item["sender"],
            recipients=_coerce_string_array(item.get("recipients", [])),
            subject=item.get("subject", ""),
            body=item["body"],
            timestamp=(
                datetime.fromisoformat(item["timestamp"])
                if item.get("timestamp")
                else None
            ),
            interaction_type=item.get("interaction_type"),
        )
        for item in _read_jsonl(path)
    ]


def load_export_bundle(directory: str | Path) -> tuple[list[Contact], list[Message]]:
    base = Path(directory)
    contacts_path = base / "contacts.jsonl"
    messages_path = base / "messages.jsonl"
    if not contacts_path.exists():
        raise FileNotFoundError(f"contacts.jsonl not found in {base}")
    if not messages_path.exists():
        raise FileNotFoundError(f"messages.jsonl not found in {base}")
    return load_contacts(contacts_path), load_messages(messages_path)
