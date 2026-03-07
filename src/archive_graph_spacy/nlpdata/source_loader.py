"""Read-only loading of canonical source inputs for nlpdata derivation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from archive_graph_spacy.io import load_export_bundle
from archive_graph_spacy.models import Contact, Message

from .databricks import DatabricksSqlClient, get_workspace_client
from .models import SourceBundle

DEFAULT_WAREHOUSE_ID = "4b799682f2bfd311"
DEFAULT_INTERACTION_TYPES = (
    "email",
    "chat",
    "fb_message",
    "dating_notification",
    "linkedin_notification",
    "payment_notification",
)


def load_source_bundle(directory: str | Path) -> SourceBundle:
    contacts, messages = load_export_bundle(directory)
    return SourceBundle(contacts=tuple(contacts), messages=tuple(messages))


def _quote_sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _ensure_list(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(item) for item in value if str(item).strip())
    if isinstance(value, list):
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


def _split_recipients(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return tuple(str(item).strip() for item in parsed if str(item).strip())
        return tuple(part.strip() for part in value.split(",") if part.strip())
    return (str(value).strip(),)


def _contact_from_row(row: dict[str, object]) -> Contact:
    return Contact(
        person_id=str(row["person_id"]),
        display_name=str(row["display_name"]),
        emails=_ensure_list(row.get("emails")),
        phones=_ensure_list(row.get("phones")),
        photo_url=None if row.get("photo_url") in (None, "") else str(row.get("photo_url")),
        entity_type=str(row.get("entity_type") or "unknown"),
    )


def _message_from_row(row: dict[str, object]) -> Message:
    timestamp = row.get("timestamp")
    return Message(
        message_id=str(row["message_id"]),
        source=str(row["source"]),
        sender=str(row.get("sender") or ""),
        recipients=_split_recipients(row.get("recipients")),
        subject=str(row.get("subject") or ""),
        body=str(row.get("body") or ""),
        timestamp=datetime.fromisoformat(str(timestamp)) if timestamp else None,
        interaction_type=None if row.get("interaction_type") in (None, "") else str(row.get("interaction_type")),
    )


def load_source_bundle_from_databricks(
    *,
    catalog: str,
    warehouse_id: str = DEFAULT_WAREHOUSE_ID,
    profile: str | None = None,
    message_limit: int | None = None,
    people_limit: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    interaction_types: tuple[str, ...] = DEFAULT_INTERACTION_TYPES,
) -> SourceBundle:
    client = DatabricksSqlClient(get_workspace_client(profile), warehouse_id)
    quoted_types = ", ".join(_quote_sql_string(value) for value in interaction_types)

    predicates = [
        f"i.interaction_type IN ({quoted_types})",
        "COALESCE(i.preview, i.subject) IS NOT NULL",
    ]
    if start_date:
        predicates.append(f"i.timestamp >= {_quote_sql_string(start_date)}")
    if end_date:
        predicates.append(f"i.timestamp < {_quote_sql_string(end_date)}")
    message_where = " AND ".join(predicates)
    message_limit_sql = f"LIMIT {message_limit}" if message_limit is not None else ""

    messages_query = f"""
        SELECT
            i.global_interaction_id AS message_id,
            COALESCE(i.source, i.interaction_type) AS source,
            i.from_email AS sender,
            i.to_email AS recipients,
            i.subject,
            COALESCE(i.preview, i.subject, '') AS body,
            CAST(i.timestamp AS STRING) AS timestamp,
            i.interaction_type
        FROM {catalog}.gold.interactions i
        WHERE {message_where}
        ORDER BY i.timestamp DESC NULLS LAST, i.global_interaction_id
        {message_limit_sql}
    """
    messages_rows = client.fetch_all(messages_query)
    messages = tuple(_message_from_row(row) for row in messages_rows if row.get("message_id"))

    people_limit_sql = f"LIMIT {people_limit}" if people_limit is not None else ""
    contacts_query = f"""
        SELECT
            p.person_id,
            p.canonical_name AS display_name,
            p.emails,
            p.phones,
            p.photo_url,
            COALESCE(o.entity_type_override, c.entity_type, 'unknown') AS entity_type
        FROM {catalog}.gold.persons p
        LEFT JOIN {catalog}.memory.entity_overrides o ON p.person_id = o.person_id
        LEFT JOIN {catalog}.gold.entity_classification c ON p.person_id = c.person_id
        WHERE COALESCE(p.canonical_person_id, p.person_id) = p.person_id
        ORDER BY COALESCE(p.interaction_count, 0) DESC, p.person_id
        {people_limit_sql}
    """
    contacts_rows = client.fetch_all(contacts_query)

    contacts = tuple(
        _contact_from_row(row)
        for row in contacts_rows
        if row.get("person_id") and row.get("display_name")
    )
    return SourceBundle(contacts=contacts, messages=messages)


def contact_index(contacts: tuple[Contact, ...]) -> dict[str, Contact]:
    return {contact.person_id: contact for contact in contacts}


def contact_email_index(contacts: tuple[Contact, ...]) -> dict[str, Contact]:
    index: dict[str, Contact] = {}
    for contact in contacts:
        for email in contact.emails:
            index[email.casefold()] = contact
    return index


def effective_person_contacts(contacts: tuple[Contact, ...]) -> tuple[Contact, ...]:
    return tuple(contact for contact in contacts if contact.entity_type == "person")
