import pytest

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

    assert len(contacts) >= 2
    assert len(messages) >= 2


def test_load_export_bundle_raises_when_contacts_missing(tmp_path) -> None:
    (tmp_path / "messages.jsonl").write_text("")
    with pytest.raises(FileNotFoundError, match="contacts.jsonl"):
        load_export_bundle(tmp_path)


def test_load_export_bundle_raises_when_messages_missing(tmp_path) -> None:
    (tmp_path / "contacts.jsonl").write_text("")
    with pytest.raises(FileNotFoundError, match="messages.jsonl"):
        load_export_bundle(tmp_path)


def test_load_messages_normalizes_string_recipients(tmp_path) -> None:
    import json

    msg = {
        "message_id": "m-str",
        "source": "email",
        "sender": "a@example.com",
        "recipients": "b@example.com",
        "body": "hi",
    }
    (tmp_path / "messages.jsonl").write_text(json.dumps(msg) + "\n")
    messages = load_messages(tmp_path / "messages.jsonl")
    assert messages[0].recipients == ("b@example.com",)
