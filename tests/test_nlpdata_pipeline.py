import json
from dataclasses import replace

from archive_graph_spacy.nlpdata.pipeline import build_pipeline_payload, run_phase_refresh, run_pipeline
from archive_graph_spacy.nlpdata.runs import meets_runtime_goal, semantic_replay_key
from archive_graph_spacy.nlpdata.source_loader import load_source_bundle
from archive_graph_spacy.models import Contact, Message
from archive_graph_spacy.nlpdata.models import SourceBundle
from archive_graph_spacy.edges.person_person import canonical_pair_id


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


def test_run_pipeline_can_defer_phase_analysis() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/phase_temporal_outputs"),
        run_scope="phase-batch",
        include_phases=False,
    )

    assert result.phases == ()
    assert result.phase_central_people == ()
    assert result.run.output_row_counts["phases"] == 0
    assert result.run.output_row_counts["phase_diagnostics"] == 0
    assert result.run.quality_metrics["phase_analysis_deferred"] is True


def test_run_phase_refresh_rebuilds_archive_wide_phases_after_batched_runs() -> None:
    bundle = load_source_bundle("data_samples/phase_temporal_outputs")
    whole = run_pipeline(bundle, run_scope="whole-scope")
    midpoint = 4
    first_batch = run_pipeline(
        replace(bundle, messages=bundle.messages[:midpoint]),
        run_scope="batch-1",
        include_phases=False,
    )
    second_batch = run_pipeline(
        replace(bundle, messages=bundle.messages[midpoint:]),
        run_scope="batch-2",
        include_phases=False,
    )

    refreshed = run_phase_refresh(
        messages=bundle.messages,
        person_links=first_batch.person_links + second_batch.person_links,
        theme_tags=first_batch.theme_tags + second_batch.theme_tags,
        person_person_edges=first_batch.person_person_edges + second_batch.person_person_edges,
        person_person_edge_evidence=(
            first_batch.person_person_edge_evidence + second_batch.person_person_edge_evidence
        ),
        run_scope="archive-wide-phases",
    )

    assert [
        (row.phase_index, row.start_at, row.end_at, row.interaction_count)
        for row in refreshed.phases
    ] == [
        (row.phase_index, row.start_at, row.end_at, row.interaction_count)
        for row in whole.phases
    ]
    assert [(row.person_id, row.rank) for row in refreshed.phase_central_people] == [
        (row.person_id, row.rank) for row in whole.phase_central_people
    ]
    assert [(row.theme, row.rank) for row in refreshed.phase_theme_summaries] == [
        (row.theme, row.rank) for row in whole.phase_theme_summaries
    ]
    assert {row.pair_id for row in refreshed.phase_pair_summaries} == {
        row.pair_id for row in whole.phase_pair_summaries
    }
    assert refreshed.phase_pair_evidence
    assert whole.phase_pair_evidence
    assert [(row.interaction_ref, row.rank) for row in refreshed.phase_representative_interactions] == [
        (row.interaction_ref, row.rank) for row in whole.phase_representative_interactions
    ]
    assert [
        (row.diagnostic_type, row.result, row.reason_code, row.sample_ref)
        for row in refreshed.phase_diagnostics
    ] == [
        (row.diagnostic_type, row.result, row.reason_code, row.sample_ref)
        for row in whole.phase_diagnostics
    ]


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
        "phases",
        "phase_central_people",
        "phase_theme_summaries",
        "phase_pair_summaries",
        "phase_pair_evidence",
        "phase_representative_interactions",
        "phase_diagnostics",
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


def test_run_pipeline_replays_legacy_relationship_review_subject_ids_without_generation_scope() -> None:
    bundle = load_source_bundle("data_samples/feedback_relationship_outputs")
    current_result = run_pipeline(bundle, run_scope="data_samples/feedback_relationship_outputs")
    current_candidate = next(
        candidate
        for candidate in current_result.candidate_assertions
        if candidate.assertion_type == "relationship_evidence_review"
    )
    legacy_bundle = SourceBundle(
        contacts=bundle.contacts,
        messages=bundle.messages,
        reviewed_assertions=(
            {
                "candidate_assertion_id": "legacy-relationship-review",
                "assertion_type": "relationship_evidence_review",
                "subject_canonical_id": "p-alice|p-bob",
                "proposed_claim": current_candidate.proposed_claim,
                "current_review_state": "accepted",
            },
        ),
        review_assertion_decisions=(),
    )

    result = run_pipeline(legacy_bundle, run_scope="data_samples/feedback_relationship_outputs")

    assert not any(
        candidate.assertion_type == "relationship_evidence_review"
        and candidate.subject_canonical_id == canonical_pair_id("p-alice", "p-bob")
        for candidate in result.candidate_assertions
    )
    assert any(
        effect.assertion_type == "relationship_evidence_review"
        and effect.result == "applied"
        and effect.subject_canonical_id == canonical_pair_id("p-alice", "p-bob")
        for effect in result.reviewed_effects
    )


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


def test_run_pipeline_replays_accepted_disambiguation_selection_as_reviewed_mention_link() -> None:
    bundle = load_source_bundle("data_samples/candidate_assertions")
    current_result = run_pipeline(bundle, run_scope="data_samples/candidate_assertions")
    current_candidate = next(
        candidate
        for candidate in current_result.candidate_assertions
        if candidate.assertion_type == "person_link_disambiguation" and "Jamie" in candidate.proposed_claim
    )
    replay_bundle = SourceBundle(
        contacts=bundle.contacts,
        messages=bundle.messages,
        reviewed_assertions=(
            {
                "candidate_assertion_id": current_candidate.candidate_assertion_id,
                "assertion_type": current_candidate.assertion_type,
                "subject_canonical_id": current_candidate.subject_canonical_id,
                "proposed_claim": current_candidate.proposed_claim,
                "current_review_state": "accepted",
                "evidence_refs": list(current_candidate.evidence_refs),
            },
        ),
        review_assertion_decisions=(
            {
                "candidate_assertion_id": current_candidate.candidate_assertion_id,
                "decision_state": "accepted",
                "evidence_snapshot": json.dumps(
                    {
                        "candidate_assertion_id": current_candidate.candidate_assertion_id,
                        "selected_person_id": "p-jamie-a",
                        "selected_person_name": "Jamie Alpha",
                    }
                ),
            },
        ),
    )

    result = run_pipeline(replay_bundle, run_scope="data_samples/candidate_assertions")

    assert any(
        link.link_origin == "reviewed"
        and link.role == "mentioned"
        and link.person_id == "p-jamie-a"
        and link.message_id == current_candidate.subject_canonical_id
        for link in result.person_links
    )
    assert any(
        effect.assertion_type == "person_link_disambiguation"
        and effect.result == "applied"
        and effect.candidate_assertion_id == current_candidate.candidate_assertion_id
        for effect in result.reviewed_effects
    )
