from archive_graph_spacy.models import Contact, Message
from archive_graph_spacy.nlpdata.person_links import derive_person_links


def test_derive_person_links_emits_explicit_and_inferred_rows() -> None:
    contacts = (
        Contact(person_id="p-alice", display_name="Alice Example", emails=("alice@example.com",), entity_type="person"),
        Contact(person_id="p-bob", display_name="Bob Example", emails=("bob@example.com",), phones=("+15550001002",), entity_type="person"),
    )
    messages = (
        Message(
            message_id="m-001",
            source="email",
            sender="carol@example.com",
            recipients=("alice@example.com",),
            subject="Dinner with Bob",
            body="Hi Alice, can you ask Bob Example to call me at +1 555 000 1002?",
        ),
    )

    mentions, links, suppressed = derive_person_links(messages, contacts, "run-1")

    assert any(link.person_id == "p-alice" and link.role == "recipient" for link in links)
    assert any(link.person_id == "p-bob" and link.role == "mentioned" for link in links)
    assert any(mention.span_text == "Bob Example" for mention in mentions)
    assert suppressed["unresolved_sender"] == 1


def test_derive_person_links_respects_effective_classification_for_explicit_links() -> None:
    contacts = (
        Contact(person_id="p-person", display_name="Real Person", emails=("person@example.com",), entity_type="person"),
        Contact(person_id="p-business", display_name="Service Desk", emails=("support@example.com",), entity_type="business"),
    )
    messages = (
        Message(
            message_id="m-002",
            source="email",
            sender="support@example.com",
            recipients=("person@example.com",),
            subject="Ticket update",
            body="Support update",
        ),
    )

    _mentions, links, suppressed = derive_person_links(messages, contacts, "run-1")

    assert all(link.person_id != "p-business" for link in links)
    assert any(link.person_id == "p-person" for link in links)
    assert suppressed["suppressed_non_person_explicit_link"] == 1


def test_derive_person_links_suppresses_low_confidence_person_matches() -> None:
    contacts = (
        Contact(person_id="p-john-a", display_name="John Alpha", emails=("john.alpha@example.com",), entity_type="person"),
        Contact(person_id="p-john-b", display_name="John Beta", emails=("john.beta@example.com",), entity_type="person"),
    )
    messages = (
        Message(
            message_id="m-003",
            source="email",
            sender="carol@example.com",
            recipients=(),
            subject="",
            body="John said hello.",
        ),
    )

    _mentions, links, suppressed = derive_person_links(messages, contacts, "run-1")

    assert not any(link.role == "mentioned" for link in links)
    assert suppressed["suppressed_low_confidence_person_link"] >= 1
