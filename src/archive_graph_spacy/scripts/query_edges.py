"""Run DuckDB queries against derived edge tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("derived_dir", type=Path, help="Directory containing derived *.jsonl tables")
    parser.add_argument(
        "--query",
        choices=sorted(PRESET_QUERIES),
        default="top_pairs",
        help="Preset query to execute",
    )
    args = parser.parse_args()

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

    rows = con.execute(PRESET_QUERIES[args.query], [str(table_path)]).fetchall()
    columns = [column[0] for column in con.description]
    for row in rows:
        print(dict(zip(columns, row, strict=False)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
