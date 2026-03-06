"""Build person-message edge rows from an export bundle."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from archive_graph_spacy.edges import (
    aggregate_person_message_edges,
    aggregate_person_person_edges,
    build_person_message_edge_evidence,
    build_person_person_edge_evidence,
)
from archive_graph_spacy.io import load_export_bundle


def build_edge_payload(export_dir: Path) -> dict[str, list[dict[str, object]]]:
    contacts, messages = load_export_bundle(export_dir)
    contact_names = {contact.person_id: contact.display_name for contact in contacts}
    contact_types = {contact.person_id: contact.entity_type for contact in contacts}

    edge_evidence = []
    for message in messages:
        edge_evidence.extend(build_person_message_edge_evidence(message, contacts))
    edges = aggregate_person_message_edges(edge_evidence)
    person_person_edge_evidence = build_person_person_edge_evidence(edges)
    person_person_edges = aggregate_person_person_edges(person_person_edge_evidence)

    return {
        "person_message_edges": [
            {
                "edge_id": edge.edge_id,
                "person_id": edge.person_id,
                "person_name": contact_names.get(edge.person_id, edge.person_id),
                "person_type": contact_types.get(edge.person_id, "unknown"),
                "message_id": edge.message_id,
                "role": edge.role,
                "confidence": edge.confidence,
                "source": edge.source,
                "strongest_evidence_type": edge.strongest_evidence_type,
                "strongest_evidence_value": edge.strongest_evidence_value,
                "evidence_count": edge.evidence_count,
            }
            for edge in edges
        ],
        "person_message_edge_evidence": [
            {
                "edge_id": row.edge_id,
                "person_id": row.person_id,
                "person_name": contact_names.get(row.person_id, row.person_id),
                "person_type": contact_types.get(row.person_id, "unknown"),
                "message_id": row.message_id,
                "role": row.role,
                "evidence_type": row.evidence_type,
                "evidence_value": row.evidence_value,
                "confidence": row.confidence,
                "source": row.source,
            }
            for row in edge_evidence
        ],
        "person_person_edges": [
            {
                "edge_id": edge.edge_id,
                "person_a_id": edge.person_a_id,
                "person_a_name": contact_names.get(edge.person_a_id, edge.person_a_id),
                "person_a_type": contact_types.get(edge.person_a_id, "unknown"),
                "person_b_id": edge.person_b_id,
                "person_b_name": contact_names.get(edge.person_b_id, edge.person_b_id),
                "person_b_type": contact_types.get(edge.person_b_id, "unknown"),
                "confidence": edge.confidence,
                "message_count": edge.message_count,
                "co_participant_count": edge.co_participant_count,
                "mention_count": edge.mention_count,
                "strongest_relationship_type": edge.strongest_relationship_type,
                "strongest_message_id": edge.strongest_message_id,
            }
            for edge in person_person_edges
        ],
        "person_person_edge_evidence": [
            {
                "edge_id": row.edge_id,
                "person_a_id": row.person_a_id,
                "person_a_name": contact_names.get(row.person_a_id, row.person_a_id),
                "person_a_type": contact_types.get(row.person_a_id, "unknown"),
                "person_b_id": row.person_b_id,
                "person_b_name": contact_names.get(row.person_b_id, row.person_b_id),
                "person_b_type": contact_types.get(row.person_b_id, "unknown"),
                "message_id": row.message_id,
                "relationship_type": row.relationship_type,
                "confidence": row.confidence,
                "source": row.source,
            }
            for row in person_person_edge_evidence
        ],
    }


def write_edge_payload(export_dir: Path, payload: dict[str, list[dict[str, object]]]) -> Path:
    outputs_dir = export_dir / "derived"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in payload.items():
        path = outputs_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
    return outputs_dir


def build_edges(export_dir: Path) -> dict[str, object]:
    payload = build_edge_payload(export_dir)
    outputs_dir = write_edge_payload(export_dir, payload)
    return {"derived_dir": str(outputs_dir), **payload}


def main() -> int:
    export_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data_exports/latest")
    result = build_edges(export_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
