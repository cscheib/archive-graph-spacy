import json

from archive_graph_spacy.nlpdata.runs import build_phase_quality_metrics, classify_scope_overlap
from archive_graph_spacy.scripts.build_nlpdata import build_nlpdata


def test_build_nlpdata_is_safe_to_rerun(tmp_path) -> None:
    export_dir = tmp_path / "sample"
    export_dir.mkdir()
    (export_dir / "contacts.jsonl").write_text(
        '{"person_id":"p-alice","display_name":"Alice Example","emails":["alice@example.com"],"entity_type":"person"}\n',
        encoding="utf-8",
    )
    (export_dir / "messages.jsonl").write_text(
        '{"message_id":"m-001","source":"email","sender":"alice@example.com","recipients":[],"subject":"Trip hotel","body":"Flight hotel trip"}\n',
        encoding="utf-8",
    )

    first = build_nlpdata(export_dir)
    second = build_nlpdata(export_dir)

    docs_path = export_dir / "derived" / "nlpdata" / "message_search_docs.jsonl"
    rows = [json.loads(line) for line in docs_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert first["status"] == "completed"
    assert second["status"] == "completed"
    assert len(rows) == 1
    assert rows[0]["message_id"] == "m-001"


def test_classify_scope_overlap_distinguishes_same_overlap_and_independent() -> None:
    assert classify_scope_overlap(("m-001",), (("m-001",),)) == "same_scope_rerun"
    assert classify_scope_overlap(("m-001", "m-002"), (("m-002", "m-003"),)) == "overlapping_scope"
    assert classify_scope_overlap(("m-001",), (("m-010",),)) == "non_overlapping_scope"


def test_build_phase_quality_metrics_reports_bounded_phase_outputs() -> None:
    metrics = build_phase_quality_metrics(
        suppressed_phase_count=1,
        phase_boundary_merged_count=1,
        phase_boundary_retained_count=2,
        phase_representative_interaction_cap=3,
        phase_pair_evidence_cap=5,
        phase_pair_evidence_phase_cap=5,
        phase_diagnostics_count=9,
    )

    assert metrics == {
        "suppressed_phase_count": 1,
        "phase_boundary_merged_count": 1,
        "phase_boundary_retained_count": 2,
        "phase_representative_interaction_cap": 3,
        "phase_pair_evidence_cap": 5,
        "phase_pair_evidence_phase_cap": 5,
        "phase_diagnostics_count": 9,
    }
