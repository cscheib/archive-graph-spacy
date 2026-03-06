from archive_graph_spacy.edges import build_person_message_edge_evidence, build_person_message_edges
from archive_graph_spacy.io import load_contacts, load_messages
from archive_graph_spacy.models import Contact, Message


def test_build_person_message_edge_evidence_includes_explicit_and_inferred_links() -> None:
    contacts = load_contacts("data_samples/sample_contacts.jsonl")
    message = load_messages("data_samples/sample_messages.jsonl")[0]

    edges = build_person_message_edge_evidence(message, contacts)

    sender_roles = [edge for edge in edges if edge.role == "sender"]
    recipient_roles = [edge for edge in edges if edge.role == "recipient"]
    mentioned_roles = [edge for edge in edges if edge.role == "mentioned"]

    assert sender_roles == []
    assert recipient_roles[0].person_id == "p-alice"
    assert recipient_roles[0].evidence_type == "header_email"
    assert any(edge.person_id == "p-bob" for edge in mentioned_roles)
    assert any(edge.evidence_type == "exact_name_match" for edge in mentioned_roles)
    assert any(edge.evidence_type == "exact_phone_match" for edge in mentioned_roles)


def test_build_person_message_edges_aggregates_evidence_by_role() -> None:
    contacts = load_contacts("data_samples/sample_contacts.jsonl")
    message = load_messages("data_samples/sample_messages.jsonl")[0]

    edges = build_person_message_edges(message, contacts)

    mentioned_edge = next(edge for edge in edges if edge.person_id == "p-bob" and edge.role == "mentioned")

    assert mentioned_edge.strongest_evidence_type in {"exact_name_match", "exact_phone_match"}
    assert mentioned_edge.evidence_count >= 2


def test_build_person_message_edge_evidence_uses_participant_context_for_ambiguous_name() -> None:
    contacts = [
        Contact(person_id="p-chris", display_name="Chris Scheib", emails=("chris@scheib.io",)),
        Contact(person_id="p-john-n", display_name="John Nissenzone", emails=("john@puppetlabs.com",)),
        Contact(person_id="p-john-m", display_name="John Marrett", emails=("john.marrett@example.com",)),
    ]
    message = Message(
        message_id="m-john",
        source="workspace_gmail",
        sender="chris@scheib.io",
        recipients=("john@puppetlabs.com",),
        subject="Puppet Meetup",
        body="Hey John,\n\nCan we do the meetup next quarter?\n",
    )

    edges = build_person_message_edge_evidence(message, contacts)
    mentioned_roles = [edge for edge in edges if edge.role == "mentioned"]

    assert any(edge.person_id == "p-john-n" and edge.confidence > 0.25 for edge in mentioned_roles)
    assert all(edge.person_id != "p-john-m" for edge in mentioned_roles)
