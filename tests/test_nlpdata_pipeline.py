from archive_graph_spacy.nlpdata.pipeline import build_pipeline_payload, run_pipeline
from archive_graph_spacy.nlpdata.runs import meets_runtime_goal
from archive_graph_spacy.nlpdata.source_loader import load_source_bundle
from archive_graph_spacy.models import Contact, Message
from archive_graph_spacy.nlpdata.models import SourceBundle


def test_run_pipeline_creates_current_rows() -> None:
    result = run_pipeline(load_source_bundle("data_samples"), run_scope="data_samples")

    assert result.run.status == "completed"
    assert len(result.mentions) >= 1
    assert len(result.person_links) >= 1
    assert result.candidate_assertions == ()
    assert result.candidate_summary.emitted_candidate_count == 0
    assert all(link.is_current for link in result.person_links)
    assert all(document.is_current for document in result.search_docs)


def test_run_pipeline_records_run_counts_and_quality_metrics() -> None:
    result = run_pipeline(load_source_bundle("data_samples"), run_scope="data_samples")

    assert result.run.output_row_counts["message_person_links"] == len(result.person_links)
    assert "runtime_seconds" in result.run.quality_metrics
    assert "meets_runtime_goal" in result.run.quality_metrics


def test_runtime_goal_helper_uses_rate_based_threshold() -> None:
    assert meets_runtime_goal(10_000, 60.0)
    assert not meets_runtime_goal(10_000, 1200.0)


def test_build_pipeline_payload_includes_all_contract_tables() -> None:
    payload = build_pipeline_payload("data_samples")

    assert set(payload) == {
        "nlp_runs",
        "message_mentions",
        "message_person_links",
        "candidate_assertions",
        "candidate_assertions_summary",
        "message_theme_tags",
        "message_search_docs",
    }


def test_run_pipeline_suppresses_system_generated_and_unresolved_results() -> None:
    bundle = SourceBundle(
        contacts=(
            Contact(
                person_id="p-person",
                display_name="Alice Example",
                emails=("alice@example.com",),
                entity_type="person",
            ),
        ),
        messages=(
            Message(
                message_id="m-system",
                source="notification",
                sender="noreply@example.com",
                recipients=(),
                subject="Support ticket",
                body="Your support issue was updated.",
                interaction_type="notification",
            ),
            Message(
                message_id="m-unresolved",
                source="email",
                sender="unknown@example.com",
                recipients=(),
                subject="",
                body="Hello there.",
            ),
        ),
    )

    result = run_pipeline(bundle, run_scope="custom-scope")

    assert result.run.quality_metrics["suppressed_system_generated_message"] >= 1
    assert result.run.quality_metrics["suppressed_system_generated_search_document"] >= 1
    assert result.run.quality_metrics["suppressed_empty_search_document"] >= 1
    assert result.search_docs == ()
