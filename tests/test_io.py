from archive_graph_spacy.io import load_contacts, load_export_bundle, load_messages


def test_load_contacts_reads_fixture() -> None:
    contacts = load_contacts("data_samples/sample_contacts.jsonl")

    assert [contact.person_id for contact in contacts] == ["p-alice", "p-bob"]
    assert contacts[0].emails == ("alice@example.com",)
    assert contacts[0].entity_type == "person"


def test_load_messages_reads_fixture() -> None:
    messages = load_messages("data_samples/sample_messages.jsonl")

    assert [message.message_id for message in messages] == ["m-001", "m-002"]
    assert messages[0].recipients == ("alice@example.com",)


def test_load_export_bundle_reads_expected_files() -> None:
    contacts, messages = load_export_bundle("data_samples")

    assert len(contacts) == 2
    assert len(messages) == 2
