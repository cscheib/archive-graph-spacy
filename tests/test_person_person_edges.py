from archive_graph_spacy.edges import (
    aggregate_person_message_edges,
    aggregate_person_person_edges,
    build_nlpdata_person_person_outputs,
    build_person_message_edge_evidence,
    build_person_person_edge_evidence,
)
from archive_graph_spacy.io import load_contacts, load_messages
from archive_graph_spacy.nlpdata.pipeline import run_pipeline
from archive_graph_spacy.nlpdata.source_loader import load_source_bundle


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


def test_build_nlpdata_person_person_outputs_creates_canonical_pair_summary_and_evidence() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/feedback_relationship_outputs"),
        run_scope="data_samples/feedback_relationship_outputs",
    )

    summaries, evidence = build_nlpdata_person_person_outputs(
        result.person_links,
        run_id=result.run.run_id,
        generation_scope="data_samples/feedback_relationship_outputs",
    )

    pair = next(row for row in summaries if row.person_a_id == "p-alice" and row.person_b_id == "p-bob")

    assert pair.direct_evidence_count >= 1
    assert pair.indirect_evidence_count >= 1
    assert pair.is_current is True
    assert any(row.pair_id == pair.pair_id and row.rank_within_pair >= 1 for row in evidence)
