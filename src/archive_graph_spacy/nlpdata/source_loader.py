"""Read-only loading of canonical source inputs for nlpdata derivation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from archive_graph_spacy.io import load_export_bundle
from archive_graph_spacy.models import Contact, Message

from .databricks import DatabricksSqlClient, DatabricksSqlError, get_workspace_client, quote_sql_identifier
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
SUPPORTED_REVIEWED_ASSERTION_TYPES = (
    "relay_sender_identity",
    "person_link_disambiguation",
    "relationship_evidence_review",
)
PAIR_SCOPED_ASSERTION_TYPES = (
    "relationship_evidence_review",
)


def load_source_bundle(directory: str | Path) -> SourceBundle:
    contacts, messages = load_export_bundle(directory)
    base = Path(directory)
    reviewed_assertions = _read_optional_jsonl(base / "reviewed_assertions.jsonl")
    review_assertion_decisions = _read_optional_jsonl(base / "review_assertion_decisions.jsonl")
    return SourceBundle(
        contacts=tuple(contacts),
        messages=tuple(messages),
        reviewed_assertions=tuple(reviewed_assertions),
        review_assertion_decisions=tuple(review_assertion_decisions),
    )


def _read_optional_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _quote_sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _message_ids_from_rows(rows: list[dict[str, object]]) -> tuple[str, ...]:
    return tuple(str(row["message_id"]) for row in rows if row.get("message_id"))


def _pair_scoped_message_ref_predicate(message_ids: tuple[str, ...]) -> str:
    if not message_ids:
        return "FALSE"
    ref_checks = ", ".join(
        _quote_sql_string(prefix + message_id)
        for message_id in message_ids
        for prefix in ("direct_message:", "indirect_message:", "message:")
    )
    return (
        f"(assertion_type IN ({', '.join(_quote_sql_string(value) for value in PAIR_SCOPED_ASSERTION_TYPES)}) "
        f"AND EXISTS(evidence_refs, ref -> ref IN ({ref_checks})))"
    )


def _is_missing_table_error(exc: DatabricksSqlError) -> bool:
    message = str(exc).casefold()
    return "table_or_view_not_found" in message or "not found" in message or "does not exist" in message


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


def source_bundle_from_rows(
    contacts_rows: list[dict[str, object]],
    message_rows: list[dict[str, object]],
    reviewed_assertion_rows: list[dict[str, object]] | None = None,
    review_assertion_decision_rows: list[dict[str, object]] | None = None,
) -> SourceBundle:
    contacts = tuple(
        _contact_from_row(row)
        for row in contacts_rows
        if row.get("person_id") and row.get("display_name")
    )
    messages = tuple(_message_from_row(row) for row in message_rows if row.get("message_id"))
    return SourceBundle(
        contacts=contacts,
        messages=messages,
        reviewed_assertions=tuple(reviewed_assertion_rows or []),
        review_assertion_decisions=tuple(review_assertion_decision_rows or []),
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
    quoted_catalog = quote_sql_identifier(catalog)
    quoted_types = ", ".join(_quote_sql_string(value) for value in interaction_types)

    predicates = [
        f"i.interaction_type IN ({quoted_types})",
        "COALESCE(i.body, i.preview, i.subject) IS NOT NULL",
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
            COALESCE(i.body, i.preview, i.subject, '') AS body,
            CAST(i.timestamp AS STRING) AS timestamp,
            i.interaction_type
        FROM {quoted_catalog}.gold.interactions i
        WHERE {message_where}
        ORDER BY i.timestamp DESC NULLS LAST, i.global_interaction_id
        {message_limit_sql}
    """
    messages_rows = client.fetch_all(messages_query)
    message_ids = _message_ids_from_rows(messages_rows)
    people_limit_sql = f"LIMIT {people_limit}" if people_limit is not None else ""
    contacts_query = f"""
        SELECT
            p.person_id,
            p.canonical_name AS display_name,
            p.emails,
            p.phones,
            p.photo_url,
            COALESCE(o.entity_type_override, c.entity_type, 'unknown') AS entity_type
        FROM {quoted_catalog}.gold.persons p
        LEFT JOIN {quoted_catalog}.memory.entity_overrides o ON p.person_id = o.person_id
        LEFT JOIN {quoted_catalog}.gold.entity_classification c ON p.person_id = c.person_id
        WHERE COALESCE(p.canonical_person_id, p.person_id) = p.person_id
        ORDER BY COALESCE(p.interaction_count, 0) DESC, p.person_id
        {people_limit_sql}
    """
    contacts_rows = client.fetch_all(contacts_query)
    if not message_ids:
        return source_bundle_from_rows(contacts_rows, messages_rows)

    quoted_supported_types = ", ".join(_quote_sql_string(value) for value in SUPPORTED_REVIEWED_ASSERTION_TYPES)
    quoted_message_ids = ", ".join(_quote_sql_string(value) for value in message_ids)
    pair_scope_predicate = _pair_scoped_message_ref_predicate(message_ids)
    reviewed_assertions_query = f"""
        SELECT
            candidate_assertion_id,
            reviewed_assertion_id,
            review_decision_id,
            assertion_type,
            subject_canonical_id,
            proposed_claim,
            current_review_state,
            promotion_eligibility,
            promotion_status,
            evidence_refs,
            provenance_summary,
            confidence_level,
            CAST(updated_at AS STRING) AS updated_at
        FROM {quoted_catalog}.memory.reviewed_assertions
        WHERE assertion_type IN ({quoted_supported_types})
          AND (
            subject_canonical_id IN ({quoted_message_ids})
            OR {pair_scope_predicate}
          )
    """
    review_assertion_decisions_query = f"""
        SELECT
            candidate_assertion_id,
            review_decision_id,
            decision_state,
            reviewer_actor,
            decision_reason,
            CAST(decision_timestamp AS STRING) AS decision_timestamp,
            evidence_snapshot,
            promotion_intent
        FROM {quoted_catalog}.memory.review_assertion_decisions
        WHERE candidate_assertion_id IN (
            SELECT candidate_assertion_id
            FROM {quoted_catalog}.memory.reviewed_assertions
            WHERE assertion_type IN ({quoted_supported_types})
              AND (
                subject_canonical_id IN ({quoted_message_ids})
                OR {pair_scope_predicate}
              )
        )
    """
    try:
        reviewed_assertion_rows = client.fetch_all(reviewed_assertions_query)
    except DatabricksSqlError as exc:
        if not _is_missing_table_error(exc):
            raise
        reviewed_assertion_rows = []
    try:
        review_assertion_decision_rows = client.fetch_all(review_assertion_decisions_query)
    except DatabricksSqlError as exc:
        if not _is_missing_table_error(exc):
            raise
        review_assertion_decision_rows = []
    return source_bundle_from_rows(
        contacts_rows,
        messages_rows,
        reviewed_assertion_rows=reviewed_assertion_rows,
        review_assertion_decision_rows=review_assertion_decision_rows,
    )


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
