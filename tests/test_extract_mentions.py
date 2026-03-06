from archive_graph_spacy.extract import extract_message_mentions
from archive_graph_spacy.io import load_messages


def test_extract_message_mentions_keeps_full_name_but_drops_greeting_noise() -> None:
    message = load_messages("data_samples/sample_messages.jsonl")[0]

    mentions = extract_message_mentions(message)
    mention_texts = {mention.text for mention in mentions}

    assert "Bob Example" in mention_texts
    assert "Hi Alice" not in mention_texts
