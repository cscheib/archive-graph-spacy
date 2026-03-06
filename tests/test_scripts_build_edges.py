import json
import subprocess


def test_build_edges_outputs_edge_rows() -> None:
    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.build_edges",
            "data_samples",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert any(edge["role"] == "recipient" for edge in payload["person_message_edges"])
    assert any(edge["person_name"] == "Alice Example" for edge in payload["person_message_edges"])
    assert any(edge["role"] == "mentioned" for edge in payload["person_message_edges"])
    assert any(
        evidence["evidence_type"] == "exact_phone_match"
        for evidence in payload["person_message_edge_evidence"]
    )
    assert any(
        edge["person_a_id"] == "p-alice"
        and edge["person_b_id"] == "p-bob"
        and edge["person_a_name"] == "Alice Example"
        and edge["person_b_name"] == "Bob Example"
        for edge in payload["person_person_edges"]
    )
    assert any(
        evidence["relationship_type"] == "message_mention"
        for evidence in payload["person_person_edge_evidence"]
    )
