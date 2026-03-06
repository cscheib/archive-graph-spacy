"""Render a simple PyVis ego network from person-person edges."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
from pyvis.network import Network

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
    <div style="margin-bottom: 6px;"><span style="color:#c2410c; font-weight:700;">Orange node</span>: focal person.</div>
    <div style="margin-bottom: 6px;"><span style="color:#2563eb; font-weight:700;">Blue node</span>: connected person.</div>
    <div style="margin-bottom: 6px;"><span style="color:#0f766e; font-weight:700;">Green edge</span>: strongest evidence is explicit co-participation.</div>
    <div style="margin-bottom: 6px;"><span style="color:#7c3aed; font-weight:700;">Purple edge</span>: strongest evidence is inferred message mention.</div>
    <div style="margin-bottom: 6px;"><span style="font-weight:700;">Distance</span>: force-layout positioning only, not a reliable closeness score.</div>
    <div><span style="font-weight:700;">Hover</span>: shows IDs, message counts, and evidence mix.</div>
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


def render_ego_graph(
    derived_dir: Path,
    person_id: str,
    output: Path,
    *,
    limit: int = 25,
) -> Path:
    edge_path = derived_dir / "person_person_edges.jsonl"
    if not edge_path.exists():
        raise SystemExit(
            f"Missing derived table: {edge_path}. Run "
            "`uv run python -m archive_graph_spacy.scripts.build_edges <export_dir>` first."
        )
    query = """
        SELECT *
        FROM read_json_auto(?)
        WHERE person_a_id = ? OR person_b_id = ?
          AND person_a_type = 'person'
          AND person_b_type = 'person'
        ORDER BY message_count DESC, confidence DESC
        LIMIT ?
    """

    con = duckdb.connect()
    rows = con.execute(query, [str(edge_path), person_id, person_id, limit]).fetchall()
    columns = [column[0] for column in con.description]
    records = [dict(zip(columns, row, strict=False)) for row in rows]
    center_label = person_id
    center_messages = 0
    center_mentions = 0
    center_co_participant = 0
    for record in records:
        center_messages += record["message_count"]
        center_mentions += record["mention_count"]
        center_co_participant += record["co_participant_count"]
        if record["person_a_id"] == person_id:
            center_label = record.get("person_a_name") or person_id
            break
        if record["person_b_id"] == person_id:
            center_label = record.get("person_b_name") or person_id
            break

    net = Network(height="800px", width="100%", bgcolor="#faf7ef", font_color="#1f2937")
    net.barnes_hut()
    center_hover = (
        f"{center_label}\n"
        f"id: {person_id}\n"
        f"shown connections: {len(records)}\n"
        f"total messages: {center_messages}\n"
        f"co-participant messages: {center_co_participant}\n"
        f"mention messages: {center_mentions}"
    )
    net.add_node(person_id, label=center_label, title=center_hover, color="#c2410c", size=28)

    for record in records:
        other = record["person_b_id"] if record["person_a_id"] == person_id else record["person_a_id"]
        other_label = (
            record.get("person_b_name")
            if record["person_a_id"] == person_id
            else record.get("person_a_name")
        ) or other
        other_hover = (
            f"{other_label}\n"
            f"id: {other}\n"
            f"messages with {center_label}: {record['message_count']}\n"
            f"co-participant messages: {record['co_participant_count']}\n"
            f"mention messages: {record['mention_count']}\n"
            f"strongest evidence: {record['strongest_relationship_type']}"
        )
        net.add_node(
            other,
            label=other_label,
            title=other_hover,
            color="#2563eb",
            size=16 + (record["message_count"] * 2),
        )
        title = (
            f"{center_label} <-> {other_label}\n"
            f"messages: {record['message_count']}\n"
            f"co-participant messages: {record['co_participant_count']}\n"
            f"mention messages: {record['mention_count']}\n"
            f"strongest evidence: {record['strongest_relationship_type']}\n"
            f"confidence: {record['confidence']}"
        )
        net.add_edge(
            person_id,
            other,
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
    parser.add_argument("person_id", help="Person ID to center the ego graph on")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ego_network.html"),
        help="HTML file to write",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum neighbor edges to include",
    )
    args = parser.parse_args()
    output = render_ego_graph(
        args.derived_dir,
        args.person_id,
        args.output,
        limit=args.limit,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
