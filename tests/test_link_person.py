from archive_graph_spacy.extract import extract_message_mentions
from archive_graph_spacy.io import load_contacts, load_messages
from archive_graph_spacy.link import link_mentions_to_people
from archive_graph_spacy.models import Contact, Mention


def test_link_mentions_to_people_scores_exact_matches() -> None:
    contacts = load_contacts("data_samples/sample_contacts.jsonl")
    message = load_messages("data_samples/sample_messages.jsonl")[0]

    results = link_mentions_to_people(extract_message_mentions(message), contacts)

    assert results["Bob Example"][0].person_id == "p-bob"
    assert "exact_name" in results["Bob Example"][0].reasons
    assert results["+1 555 000 1002"][0].person_id == "p-bob"
    assert "exact_phone" in results["+1 555 000 1002"][0].reasons


def test_link_mentions_to_people_ignores_non_phone_text_for_phone_matches() -> None:
    contacts = load_contacts("data_samples/sample_contacts.jsonl")

    results = link_mentions_to_people(
        [Mention(text="Hey", label="PERSON_CANDIDATE", source="heuristic")],
        contacts,
    )

    assert results == {}


def test_link_mentions_to_people_prefers_explicit_participant_for_ambiguous_first_name() -> None:
    contacts = [
        Contact(person_id="p-john-n", display_name="John Nissenzone", emails=("john@puppetlabs.com",)),
        Contact(person_id="p-john-m", display_name="John Marrett", emails=("john.marrett@example.com",)),
    ]

    results = link_mentions_to_people(
        [Mention(text="John", label="PERSON_CANDIDATE", source="heuristic")],
        contacts,
        preferred_person_ids={"p-john-n"},
    )

    assert results["John"][0].person_id == "p-john-n"
    assert results["John"][0].score > 0.25
    assert "explicit_participant_context" in results["John"][0].reasons
    assert [candidate.person_id for candidate in results["John"]] == ["p-john-n"]
