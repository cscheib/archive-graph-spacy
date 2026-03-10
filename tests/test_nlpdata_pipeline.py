from archive_graph_spacy.nlpdata.pipeline import build_pipeline_payload, run_pipeline
from archive_graph_spacy.nlpdata.runs import meets_runtime_goal, semantic_replay_key
from archive_graph_spacy.nlpdata.source_loader import load_source_bundle
from archive_graph_spacy.models import Contact, Message
from archive_graph_spacy.nlpdata.models import SourceBundle


def test_run_pipeline_creates_current_rows() -> None:
    result = run_pipeline(load_source_bundle("data_samples"), run_scope="data_samples")

    assert result.run.status == "completed"
    assert len(result.mentions) >= 1
    assert len(result.person_links) >= 1
    assert result.candidate_summary.emitted_candidate_count == len(result.candidate_assertions)
    assert {candidate.assertion_type for candidate in result.candidate_assertions} == {"relationship_evidence_review"}
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
        "reviewed_effects",
        "person_person_edges",
        "person_person_edge_evidence",
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


def test_run_pipeline_consumes_reviewed_feedback_and_emits_pair_outputs() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/feedback_relationship_outputs"),
        run_scope="data_samples/feedback_relationship_outputs",
    )

    candidate_types = {candidate.assertion_type for candidate in result.candidate_assertions}
    reviewed_by_result = {effect.result for effect in result.reviewed_effects}

    assert "relay_sender_identity" in candidate_types
    assert "relationship_evidence_review" in candidate_types
    assert "applied" in reviewed_by_result
    assert "suppressed" in reviewed_by_result
    assert result.candidate_summary.reviewed_effect_counts["applied"] >= 1
    assert result.candidate_summary.reviewed_effect_counts["suppressed"] >= 1
    assert any(link.link_origin == "reviewed" and link.role == "sender" for link in result.person_links)
    assert any(edge.person_a_id == "p-alice" and edge.person_b_id == "p-bob" for edge in result.person_person_edges)
    assert any(row.evidence_family == "message_mention" for row in result.person_person_edge_evidence)


def test_semantic_replay_key_tolerates_mention_identifier_drift() -> None:
    first = semantic_replay_key(
        assertion_type="person_link_disambiguation",
        subject_canonical_id="m-ambiguous-jamie",
        proposed_claim="mention mm-123abc 'Jamie' is ambiguous across p-jamie-a, p-jamie-b",
        generation_scope="scope-a",
    )
    second = semantic_replay_key(
        assertion_type="person_link_disambiguation",
        subject_canonical_id="m-ambiguous-jamie",
        proposed_claim="mention im-b7d27d726aae 'Jamie' is ambiguous across p-jamie-a, p-jamie-b",
        generation_scope="scope-a",
    )

    assert first == second


def test_semantic_replay_key_separates_generation_scopes() -> None:
    first = semantic_replay_key(
        assertion_type="relay_sender_identity",
        subject_canonical_id="m-relay-bob",
        proposed_claim="relay sender relay+bob@relay.example.com maps to p-bob",
        generation_scope="scope-a",
    )
    second = semantic_replay_key(
        assertion_type="relay_sender_identity",
        subject_canonical_id="m-relay-bob",
        proposed_claim="relay sender relay+bob@relay.example.com maps to p-bob",
        generation_scope="scope-b",
    )

    assert first != second
