from archive_graph_spacy.models import Contact, Message
from archive_graph_spacy.nlpdata.person_links import derive_person_links
from archive_graph_spacy.nlpdata.search_docs import _tokenize, build_search_documents, query_search_documents
from archive_graph_spacy.nlpdata.themes import derive_theme_tags


def test_build_search_documents_combines_links_without_full_text_duplication() -> None:
    contacts = (
        Contact(person_id="p-alice", display_name="Alice Example", emails=("alice@example.com",), entity_type="person"),
        Contact(person_id="p-bob", display_name="Bob Example", emails=("bob@example.com",), phones=("+15550001002",), entity_type="person"),
    )
    messages = (
        Message(
            message_id="m-001",
            source="email",
            sender="alice@example.com",
            recipients=("bob@example.com",),
            subject="Trip plans",
            body="Bob Example booked the flight and hotel.",
        ),
    )
    _mentions, links, _suppressed = derive_person_links(messages, contacts, "run-1")
    themes, _ = derive_theme_tags(messages, "run-1")

    documents, suppressed = build_search_documents(messages, links, themes, "run-1")

    assert len(documents) == 1
    document = documents[0]
    assert document.message_id == "m-001"
    assert "p-alice" in document.explicit_person_ids
    assert "p-bob" in document.explicit_person_ids
    assert "travel" in document.theme_labels
    assert not hasattr(document, "body")
    assert suppressed["suppressed_empty_search_document"] == 0


def test_query_search_documents_filters_by_person_and_theme() -> None:
    contacts = (
        Contact(person_id="p-alice", display_name="Alice Example", emails=("alice@example.com",), entity_type="person"),
        Contact(person_id="p-bob", display_name="Bob Example", emails=("bob@example.com",), entity_type="person"),
    )
    messages = (
        Message(
            message_id="m-010",
            source="email",
            sender="alice@example.com",
            recipients=("bob@example.com",),
            subject="Family trip",
            body="The family flight is booked.",
        ),
        Message(
            message_id="m-011",
            source="email",
            sender="alice@example.com",
            recipients=("bob@example.com",),
            subject="Project update",
            body="The client meeting moved.",
        ),
    )
    _mentions, links, _suppressed = derive_person_links(messages, contacts, "run-1")
    themes, _ = derive_theme_tags(messages, "run-1")
    documents, _ = build_search_documents(messages, links, themes, "run-1")

    results = query_search_documents(documents, person_id="p-bob", theme="family")

    assert [document.message_id for document in results] == ["m-010"]


def test_build_search_documents_omits_suppressed_theme_rows() -> None:
    contacts = (
        Contact(person_id="p-alice", display_name="Alice Example", emails=("alice@example.com",), entity_type="person"),
    )
    messages = (
        Message(
            message_id="m-020",
            source="email",
            sender="alice@example.com",
            recipients=(),
            subject="Trip",
            body="Soon",
        ),
    )
    _mentions, links, _suppressed = derive_person_links(messages, contacts, "run-1")
    themes, suppressed_themes = derive_theme_tags(messages, "run-1")
    documents, _ = build_search_documents(messages, links, themes, "run-1")

    assert themes == ()
    assert suppressed_themes["suppressed_low_confidence_theme"] >= 1
    assert documents[0].theme_labels == ()


def test_tokenize_preserves_first_seen_order_while_deduping() -> None:
    assert _tokenize("Alice met Bob and Alice met Carol") == ("alice", "met", "bob", "and", "carol")
