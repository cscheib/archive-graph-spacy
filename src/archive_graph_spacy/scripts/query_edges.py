"""Run DuckDB queries against derived edge tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from archive_graph_spacy.config import get_owner_person_id


VALID_OWNER_MODES = ("normal", "downrank", "hide")
DEFAULT_OWNER_MODE = "downrank"

PRESET_QUERIES = {
    "top_pairs": """
        SELECT
            person_a_name,
            person_a_id,
            person_b_name,
            person_b_id,
            message_count,
            mention_count,
            co_participant_count
        FROM read_json_auto(?)
        WHERE person_a_type = 'person'
          AND person_b_type = 'person'
        ORDER BY message_count DESC, mention_count DESC, person_a_name, person_b_name
        LIMIT 20
    """,
    "top_mentions": """
        SELECT person_name, person_id, COUNT(*) AS mention_edges
        FROM read_json_auto(?)
        WHERE role = 'mentioned'
          AND person_type = 'person'
        GROUP BY person_name, person_id
        ORDER BY mention_edges DESC, person_name
        LIMIT 20
    """,
}


def _top_mentions_query(owner_person_id: str | None, owner_mode: str) -> str:
    filters = [
        "role = 'mentioned'",
        "person_type = 'person'",
    ]
    if owner_person_id and owner_mode == "hide":
        filters.append("person_id != ?")

    order_by = "mention_edges DESC, person_name"
    if owner_person_id and owner_mode == "downrank":
        order_by = "CASE WHEN person_id = ? THEN 1 ELSE 0 END ASC, " + order_by

    return f"""
        SELECT person_name, person_id, COUNT(*) AS mention_edges
        FROM read_json_auto(?)
        WHERE {" AND ".join(filters)}
        GROUP BY person_name, person_id
        ORDER BY {order_by}
        LIMIT 20
    """


def _top_pairs_query(owner_person_id: str | None, owner_mode: str) -> str:
    filters = [
        "person_a_type = 'person'",
        "person_b_type = 'person'",
    ]
    if owner_person_id and owner_mode == "hide":
        filters.append("person_a_id != ?")
        filters.append("person_b_id != ?")

    order_by = "message_count DESC, mention_count DESC, person_a_name, person_b_name"
    if owner_person_id and owner_mode == "downrank":
        order_by = (
            "CASE WHEN person_a_id = ? OR person_b_id = ? THEN 1 ELSE 0 END ASC, "
            + order_by
        )

    return f"""
        SELECT
            person_a_name,
            person_a_id,
            person_b_name,
            person_b_id,
            message_count,
            mention_count,
            co_participant_count
        FROM read_json_auto(?)
        WHERE {" AND ".join(filters)}
        ORDER BY {order_by}
        LIMIT 20
    """


def _query_sql_and_params(
    query_name: str,
    table_path: Path,
    owner_person_id: str | None,
    owner_mode: str,
) -> tuple[str, list[str]]:
    params: list[str] = [str(table_path)]
    if query_name == "top_mentions":
        if owner_person_id and owner_mode == "hide":
            params.extend([owner_person_id])
        if owner_person_id and owner_mode == "downrank":
            params.extend([owner_person_id])
        return _top_mentions_query(owner_person_id, owner_mode), params

    if query_name != "top_pairs":
        return PRESET_QUERIES[query_name], params

    if owner_person_id and owner_mode == "hide":
        params.extend([owner_person_id, owner_person_id])
    if owner_person_id and owner_mode == "downrank":
        params.extend([owner_person_id, owner_person_id])
    return _top_pairs_query(owner_person_id, owner_mode), params


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("derived_dir", type=Path, help="Directory containing derived *.jsonl tables")
    parser.add_argument(
        "--query",
        choices=sorted(PRESET_QUERIES),
        default="top_pairs",
        help="Preset query to execute",
    )
    parser.add_argument(
        "--owner-person-id",
        help="Optional owner person_id to hide or downrank in top_pairs",
    )
    parser.add_argument(
        "--owner-mode",
        choices=VALID_OWNER_MODES,
        default=DEFAULT_OWNER_MODE,
        help="How to treat the owner in top_pairs results",
    )
    args = parser.parse_args()
    owner_person_id = args.owner_person_id or get_owner_person_id()

    derived_dir = args.derived_dir
    con = duckdb.connect()

    if args.query == "top_pairs":
        table_path = derived_dir / "person_person_edges.jsonl"
    else:
        table_path = derived_dir / "person_message_edges.jsonl"

    if not table_path.exists():
        raise SystemExit(
            f"Missing derived table: {table_path}. Run "
            "`uv run python -m archive_graph_spacy.scripts.build_edges <export_dir>` first."
        )

    sql, params = _query_sql_and_params(
        args.query,
        table_path,
        owner_person_id,
        args.owner_mode,
    )
    rows = con.execute(sql, params).fetchall()
    columns = [column[0] for column in con.description]
    for row in rows:
        print(dict(zip(columns, row, strict=False)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
