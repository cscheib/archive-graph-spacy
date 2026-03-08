from archive_graph_spacy.models import Message
from archive_graph_spacy.nlpdata.themes import derive_theme_tags, is_system_generated_message


def test_derive_theme_tags_publishes_high_confidence_rule_matches() -> None:
    messages = (
        Message(
            message_id="m-100",
            source="email",
            sender="alice@example.com",
            recipients=(),
            subject="Family trip hotel",
            body="The family flight and hotel are booked for the trip.",
        ),
    )

    themes, suppressed = derive_theme_tags(messages, "run-1")

    assert any(theme.theme == "family" for theme in themes)
    assert any(theme.theme == "travel" for theme in themes)
    assert suppressed == {}


def test_derive_theme_tags_suppresses_system_generated_messages() -> None:
    message = Message(
        message_id="m-101",
        source="notification",
        sender="noreply@example.com",
        recipients=(),
        subject="Support ticket",
        body="Your support ticket was updated.",
        interaction_type="notification",
    )

    themes, suppressed = derive_theme_tags((message,), "run-1")

    assert is_system_generated_message(message)
    assert themes == ()
    assert suppressed["suppressed_system_generated_message"] == 1
