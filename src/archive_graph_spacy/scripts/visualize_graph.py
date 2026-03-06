"""Render a person-only PyVis graph from person-person edges."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
from pyvis.network import Network

from archive_graph_spacy.config import get_owner_person_id

VALID_OWNER_MODES = ("normal", "downrank", "hide")
DEFAULT_OWNER_MODE = "downrank"

LEGEND_HTML = """
<div style="
    position: fixed;
    top: 16px;
    right: 16px;
    z-index: 9999;
    width: 320px;
    background: rgba(250, 247, 239, 0.96);
    border: 1px solid #d6d3d1;
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
    font-family: sans-serif;
    color: #1f2937;
">
  <div style="font-size: 16px; font-weight: 700; margin-bottom: 8px;">Graph Guide</div>
  <div style="font-size: 13px; line-height: 1.45;">
    <div style="margin-bottom: 6px;"><span style="color:#0f766e; font-weight:700;">Green edge</span>: strongest evidence is explicit co-participation.</div>
    <div style="margin-bottom: 6px;"><span style="color:#7c3aed; font-weight:700;">Purple edge</span>: strongest evidence is inferred message mention.</div>
    <div style="margin-bottom: 6px;"><span style="font-weight:700;">Node size</span>: total message volume across shown edges.</div>
    <div style="margin-bottom: 6px;"><span style="font-weight:700;">Distance</span>: force-layout positioning only, not a reliable closeness score.</div>
    <div><span style="font-weight:700;">Hover</span>: shows IDs, edge counts, and evidence mix.</div>
  </div>
</div>
"""

TOOLTIP_STYLE = """
<style>
.vis-tooltip {
  white-space: pre-line !important;
  max-width: 360px;
}
</style>
"""


def render_graph(
    derived_dir: Path,
    output: Path,
    *,
    limit: int = 250,
    min_messages: int = 1,
    owner_person_id: str | None = None,
    owner_mode: str = DEFAULT_OWNER_MODE,
) -> Path:
    edge_path = derived_dir / "person_person_edges.jsonl"
    if not edge_path.exists():
        raise SystemExit(
            f"Missing derived table: {edge_path}. Run "
            "`uv run python -m archive_graph_spacy.scripts.build_edges <export_dir>` first."
        )

    filters = [
        "person_a_type = 'person'",
        "person_b_type = 'person'",
        "message_count >= ?",
    ]
    params: list[object] = [str(edge_path), min_messages]
    if owner_person_id and owner_mode == "hide":
        filters.extend(["person_a_id != ?", "person_b_id != ?"])
        params.extend([owner_person_id, owner_person_id])

    order_by = "message_count DESC, confidence DESC, person_a_name, person_b_name"
    if owner_person_id and owner_mode == "downrank":
        order_by = (
            "CASE WHEN person_a_id = ? OR person_b_id = ? THEN 1 ELSE 0 END ASC, "
            + order_by
        )
        params.extend([owner_person_id, owner_person_id])

    query = f"""
        SELECT *
        FROM read_json_auto(?)
        WHERE {' AND '.join(filters)}
        ORDER BY {order_by}
        LIMIT ?
    """
    params.append(limit)

    con = duckdb.connect()
    rows = con.execute(query, params).fetchall()
    columns = [column[0] for column in con.description]
    records = [dict(zip(columns, row, strict=False)) for row in rows]

    net = Network(height="900px", width="100%", bgcolor="#faf7ef", font_color="#1f2937")
    net.barnes_hut()

    node_weights: dict[str, int] = {}
    node_labels: dict[str, str] = {}
    node_connection_counts: dict[str, int] = {}
    node_co_participant_counts: dict[str, int] = {}
    node_mention_counts: dict[str, int] = {}
    for record in records:
        node_weights[record["person_a_id"]] = node_weights.get(record["person_a_id"], 0) + record["message_count"]
        node_weights[record["person_b_id"]] = node_weights.get(record["person_b_id"], 0) + record["message_count"]
        node_labels[record["person_a_id"]] = record.get("person_a_name") or record["person_a_id"]
        node_labels[record["person_b_id"]] = record.get("person_b_name") or record["person_b_id"]
        node_connection_counts[record["person_a_id"]] = node_connection_counts.get(record["person_a_id"], 0) + 1
        node_connection_counts[record["person_b_id"]] = node_connection_counts.get(record["person_b_id"], 0) + 1
        node_co_participant_counts[record["person_a_id"]] = (
            node_co_participant_counts.get(record["person_a_id"], 0) + record["co_participant_count"]
        )
        node_co_participant_counts[record["person_b_id"]] = (
            node_co_participant_counts.get(record["person_b_id"], 0) + record["co_participant_count"]
        )
        node_mention_counts[record["person_a_id"]] = (
            node_mention_counts.get(record["person_a_id"], 0) + record["mention_count"]
        )
        node_mention_counts[record["person_b_id"]] = (
            node_mention_counts.get(record["person_b_id"], 0) + record["mention_count"]
        )

    for person_id, label in node_labels.items():
        weight = node_weights.get(person_id, 1)
        hover = (
            f"{label}\n"
            f"id: {person_id}\n"
            f"shown edges: {node_connection_counts.get(person_id, 0)}\n"
            f"total messages: {weight}\n"
            f"co-participant messages: {node_co_participant_counts.get(person_id, 0)}\n"
            f"mention messages: {node_mention_counts.get(person_id, 0)}"
        )
        net.add_node(
            person_id,
            label=label,
            title=hover,
            color="#2563eb",
            size=14 + min(weight, 30),
        )

    for record in records:
        title = (
            f"{record['person_a_name']} <-> {record['person_b_name']}\n"
            f"messages: {record['message_count']}\n"
            f"co-participant messages: {record['co_participant_count']}\n"
            f"mention messages: {record['mention_count']}\n"
            f"strongest evidence: {record['strongest_relationship_type']}\n"
            f"confidence: {record['confidence']}"
        )
        net.add_edge(
            record["person_a_id"],
            record["person_b_id"],
            value=max(record["message_count"], 1),
            title=title,
            color="#0f766e" if record["strongest_relationship_type"] == "co_participant" else "#7c3aed",
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(output), open_browser=False, notebook=False)
    html = output.read_text(encoding="utf-8")
    if "</body>" in html:
        html = html.replace("</body>", TOOLTIP_STYLE + "\n" + LEGEND_HTML + "\n</body>")
        output.write_text(html, encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("derived_dir", type=Path, help="Directory containing derived edge tables")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("network_graph.html"),
        help="HTML file to write",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=250,
        help="Maximum number of edges to include",
    )
    parser.add_argument(
        "--min-messages",
        type=int,
        default=1,
        help="Minimum message_count required to include an edge",
    )
    parser.add_argument(
        "--owner-person-id",
        help="Optional owner person_id to hide or downrank in the graph",
    )
    parser.add_argument(
        "--owner-mode",
        choices=VALID_OWNER_MODES,
        default=DEFAULT_OWNER_MODE,
        help="How to treat the owner in the graph",
    )
    args = parser.parse_args()
    owner_person_id = args.owner_person_id or get_owner_person_id()
    output = render_graph(
        args.derived_dir,
        args.output,
        limit=args.limit,
        min_messages=args.min_messages,
        owner_person_id=owner_person_id,
        owner_mode=args.owner_mode,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
