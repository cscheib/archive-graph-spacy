from archive_graph_spacy.edges import (
    aggregate_person_message_edges,
    aggregate_person_person_edges,
    build_person_message_edge_evidence,
    build_person_person_edge_evidence,
)
from archive_graph_spacy.io import load_contacts, load_messages


def test_build_person_person_edges_projects_relationships_from_messages() -> None:
    contacts = load_contacts("data_samples/sample_contacts.jsonl")
    messages = load_messages("data_samples/sample_messages.jsonl")

    person_message_evidence = []
    for message in messages:
        person_message_evidence.extend(build_person_message_edge_evidence(message, contacts))
    person_message_edges = aggregate_person_message_edges(person_message_evidence)

    evidence = build_person_person_edge_evidence(person_message_edges)
    edges = aggregate_person_person_edges(evidence)

    pair = next(edge for edge in edges if edge.person_a_id == "p-alice" and edge.person_b_id == "p-bob")

    assert pair.message_count == 2
    assert pair.co_participant_count == 1
    assert pair.mention_count == 2
    assert pair.confidence == 1.0
