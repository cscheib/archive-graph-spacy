from __future__ import annotations

from archive_graph_spacy.models import Contact, Message
from archive_graph_spacy.edges.person_person import canonical_pair_id
from archive_graph_spacy.nlpdata.pipeline import build_pipeline_payload, run_pipeline
from archive_graph_spacy.nlpdata.person_links import _normalized_reviewed_inputs, derive_candidate_assertions
from archive_graph_spacy.nlpdata.source_loader import load_source_bundle


def test_relay_sender_candidates_include_required_review_fields() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/candidate_assertions"),
        run_scope="data_samples/candidate_assertions",
    )

    relay_candidates = [
        candidate
        for candidate in result.candidate_assertions
        if candidate.assertion_type == "relay_sender_identity"
    ]

    assert len(relay_candidates) == 2
    assert {candidate.review_class for candidate in relay_candidates} == {"reviewable"}
    assert {candidate.promotion_class for candidate in relay_candidates} == {"promotion_eligible"}
    assert all(candidate.subject_canonical_id.startswith("m-relay-") for candidate in relay_candidates)
    assert all(any(ref.startswith("sender:relay+") for ref in candidate.evidence_refs) for candidate in relay_candidates)
    assert all("Derived from unresolved sender plus inferred link" in candidate.provenance_summary for candidate in relay_candidates)


def test_disambiguation_candidates_only_emit_for_multi_candidate_no_clear_winner_cases() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/candidate_assertions"),
        run_scope="data_samples/candidate_assertions",
    )

    disambiguation_candidates = [
        candidate
        for candidate in result.candidate_assertions
        if candidate.assertion_type == "person_link_disambiguation"
    ]

    assert len(disambiguation_candidates) == 3
    assert all(candidate.review_class == "reviewable" for candidate in disambiguation_candidates)
    assert all(candidate.promotion_class == "derived_only" for candidate in disambiguation_candidates)
    assert any("Alex" in candidate.proposed_claim for candidate in disambiguation_candidates)
    assert any("Jamie" in candidate.proposed_claim for candidate in disambiguation_candidates)
    assert any("Sam" in candidate.proposed_claim for candidate in disambiguation_candidates)
    assert all("Morgan" not in candidate.proposed_claim for candidate in disambiguation_candidates)
    assert all("Alice Example" not in candidate.proposed_claim for candidate in disambiguation_candidates)


def test_candidate_payload_publishes_jsonl_and_summary_contract_surfaces() -> None:
    payload = build_pipeline_payload("data_samples/candidate_assertions")

    assert "candidate_assertions" in payload
    assert "candidate_assertions_summary" in payload
    assert len(payload["candidate_assertions"]) == 5
    assert payload["candidate_assertions_summary"]["emitted_candidate_count"] == 5
    assert payload["candidate_assertions_summary"]["candidate_counts_by_type"] == {
        "person_link_disambiguation": 3,
        "relay_sender_identity": 2,
    }
    assert payload["candidate_assertions_summary"]["suppressed_counts"] == {
        "suppressed_disambiguation_low_value": 3,
    }
    assert len(payload["candidate_assertions_summary"]["example_candidate_ids"]) == 5


def test_repeated_ambiguous_mentions_emit_distinct_candidates() -> None:
    contacts = (
        Contact(person_id="p-alex-a", display_name="Alex Alpha", emails=("alex.alpha@example.com",), entity_type="person"),
        Contact(person_id="p-alex-b", display_name="Alex Beta", emails=("alex.beta@example.com",), entity_type="person"),
    )
    messages = (
        Message(
            message_id="m-repeat",
            source="chat",
            sender="coordinator@example.com",
            recipients=(),
            subject="",
            body="Alex said Alex will send the notes.",
        ),
    )

    candidates, summary = derive_candidate_assertions(
        messages,
        contacts,
        run_id="run-1",
        generation_scope="repeat-scope",
    )

    assert len(candidates) == 2
    assert candidates[0].candidate_assertion_id != candidates[1].candidate_assertion_id
    assert candidates[0].proposed_claim != candidates[1].proposed_claim
    assert all(any(ref.startswith("mention:") for ref in candidate.evidence_refs) for candidate in candidates)
    assert summary.emitted_candidate_count == 2


def test_relationship_evidence_review_candidates_use_shared_candidate_contract() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/feedback_relationship_outputs"),
        run_scope="data_samples/feedback_relationship_outputs",
    )

    candidates = [
        candidate
        for candidate in result.candidate_assertions
        if candidate.assertion_type == "relationship_evidence_review"
    ]

    assert len(candidates) == 1
    assert candidates[0].review_class == "reviewable"
    assert candidates[0].promotion_class == "derived_only"
    assert any(ref.startswith("pair:") for ref in candidates[0].evidence_refs)
    assert any(ref.startswith("pair_id:pair-") for ref in candidates[0].evidence_refs)
    assert candidates[0].subject_canonical_id.startswith("pair-")


def test_normalized_reviewed_inputs_parses_stringified_evidence_refs() -> None:
    reviewed = _normalized_reviewed_inputs(
        (
            {
                "candidate_assertion_id": "ca-1",
                "assertion_type": "relay_sender_identity",
                "subject_canonical_id": "m-1",
                "proposed_claim": "relay sender relay+one@example.com maps to p-1",
                "current_review_state": "accepted",
                "evidence_refs": '["message:m-1","sender:relay+one@example.com"]',
            },
        ),
        (),
    )

    assert reviewed[0]["evidence_refs"] == ("message:m-1", "sender:relay+one@example.com")


def test_normalized_reviewed_inputs_merges_selected_person_from_decision_snapshot() -> None:
    reviewed = _normalized_reviewed_inputs(
        (
            {
                "candidate_assertion_id": "ca-2",
                "assertion_type": "person_link_disambiguation",
                "subject_canonical_id": "m-2",
                "proposed_claim": "mention mm-2 'Chris' is ambiguous across p-a, p-b",
                "current_review_state": "accepted",
                "evidence_refs": ["message:m-2", "mention:mm-2"],
            },
        ),
        (
            {
                "candidate_assertion_id": "ca-2",
                "decision_state": "accepted",
                "evidence_snapshot": '{"selected_person_id":"p-b","selected_person_name":"Chris Beta"}',
            },
        ),
    )

    assert reviewed[0]["selected_person_id"] == "p-b"
    assert reviewed[0]["selected_person_name"] == "Chris Beta"


def test_relationship_evidence_candidates_share_phase3_pair_id_helper() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/feedback_relationship_outputs"),
        run_scope="data_samples/feedback_relationship_outputs",
    )

    candidate = next(
        candidate
        for candidate in result.candidate_assertions
        if candidate.assertion_type == "relationship_evidence_review"
    )

    assert candidate.subject_canonical_id == canonical_pair_id("p-alice", "p-bob")
