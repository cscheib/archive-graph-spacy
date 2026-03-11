import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from archive_graph_spacy.models import Contact, Message
from archive_graph_spacy.nlpdata.models import SourceBundle
from archive_graph_spacy.nlpdata.pipeline import build_pipeline_payload, run_pipeline
from archive_graph_spacy.nlpdata.source_loader import load_source_bundle


def _payload_rows(payload: dict[str, object], table_name: str) -> list[dict[str, object]]:
    rows = payload[table_name]
    assert isinstance(rows, list)
    return rows


def test_run_pipeline_derives_stable_phase_rows_for_bounded_fixture() -> None:
    bundle = load_source_bundle("data_samples/phase_temporal_outputs")

    first = run_pipeline(bundle, run_scope="data_samples/phase_temporal_outputs")
    second = run_pipeline(bundle, run_scope="data_samples/phase_temporal_outputs")

    assert len(first.phases) == 2
    assert [row.phase_id for row in first.phases] == [row.phase_id for row in second.phases]
    assert [row.phase_index for row in first.phases] == [1, 2]
    assert first.phases[0].start_at == "2024-01-01T10:00:00+00:00"
    assert first.phases[0].end_at == "2024-01-21T11:00:00+00:00"
    assert first.phases[1].start_at == "2024-03-11T08:00:00+00:00"
    assert first.phases[1].end_at == "2024-03-12T09:30:00+00:00"
    assert all(row.is_current for row in first.phases)
    assert len(first.phase_representative_interactions) >= 2


def test_run_pipeline_derives_phase_child_tables() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/phase_temporal_outputs"),
        run_scope="data_samples/phase_temporal_outputs",
    )

    phase_ids = {row.phase_id for row in result.phases}
    assert phase_ids
    assert all(row.phase_id in phase_ids for row in result.phase_central_people)
    assert all(row.phase_id in phase_ids for row in result.phase_theme_summaries)
    assert all(row.phase_id in phase_ids for row in result.phase_pair_summaries)
    assert all(row.phase_id in phase_ids for row in result.phase_pair_evidence)
    assert any(row.person_id == "p-alice" for row in result.phase_central_people)
    assert any(row.theme == "travel" for row in result.phase_theme_summaries)
    assert any(row.theme == "work" for row in result.phase_theme_summaries)
    assert any(row.pair_id for row in result.phase_pair_summaries)
    assert all(row.run_id == result.run.run_id for row in result.phase_pair_evidence)
    assert any(row.evidence_family == "direct_participation" for row in result.phase_pair_evidence)


def test_run_pipeline_records_boundary_and_suppression_diagnostics() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/phase_temporal_outputs"),
        run_scope="data_samples/phase_temporal_outputs",
    )

    assert any(row.diagnostic_type == "boundary" and row.result == "merged" for row in result.phase_diagnostics)
    assert any(row.diagnostic_type == "boundary" and row.result == "retained" for row in result.phase_diagnostics)
    assert any(row.diagnostic_type == "suppression" and row.result == "suppressed" for row in result.phase_diagnostics)
    phase_ids = {row.phase_id for row in result.phases}
    assert all(
        row.phase_id in phase_ids
        for row in result.phase_diagnostics
        if row.diagnostic_type == "boundary"
    )
    assert result.run.output_row_counts["phases"] == len(result.phases)
    assert result.run.output_row_counts["phase_diagnostics"] == len(result.phase_diagnostics)
    assert result.run.quality_metrics["suppressed_phase_count"] >= 1


def test_run_pipeline_retains_fractional_day_boundary_thresholds() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/phase_temporal_outputs"),
        run_scope="data_samples/phase_temporal_outputs",
    )

    retained = [
        row for row in result.phase_diagnostics if row.diagnostic_type == "boundary" and row.result == "retained"
    ]
    merged = [
        row for row in result.phase_diagnostics if row.diagnostic_type == "boundary" and row.result == "merged"
    ]

    assert any("49.875" in row.details for row in retained)
    assert any("18.250" in row.details for row in merged)


def test_phase_outputs_remain_bounded() -> None:
    result = run_pipeline(
        load_source_bundle("data_samples/phase_temporal_outputs"),
        run_scope="data_samples/phase_temporal_outputs",
    )

    phase_ids = {row.phase_id for row in result.phases}
    for phase_id in phase_ids:
        assert len([row for row in result.phase_representative_interactions if row.phase_id == phase_id]) <= 3
        assert len([row for row in result.phase_central_people if row.phase_id == phase_id]) <= 5
        assert len([row for row in result.phase_theme_summaries if row.phase_id == phase_id]) <= 5
        assert len([row for row in result.phase_pair_evidence if row.phase_id == phase_id]) <= 5
        phase_pair_ids_with_evidence = {
            row.phase_pair_id
            for row in result.phase_pair_evidence
            if row.phase_id == phase_id
        }
        assert all(
            row.phase_pair_id in phase_pair_ids_with_evidence
            for row in result.phase_pair_summaries
            if row.phase_id == phase_id
        )
    assert len(result.phase_diagnostics) <= 16


def test_build_pipeline_payload_includes_phase_outputs() -> None:
    payload = build_pipeline_payload("data_samples/phase_temporal_outputs")

    assert set(payload) >= {
        "phases",
        "phase_central_people",
        "phase_theme_summaries",
        "phase_pair_summaries",
        "phase_pair_evidence",
        "phase_representative_interactions",
        "phase_diagnostics",
    }
    assert len(_payload_rows(payload, "phases")) == 2
    assert any(row["result"] == "suppressed" for row in _payload_rows(payload, "phase_diagnostics"))


def test_build_nlpdata_writes_phase_outputs_for_phase4_fixture(tmp_path: Path) -> None:
    from archive_graph_spacy.scripts.build_nlpdata import build_nlpdata

    export_dir = tmp_path / "phase_temporal_outputs"
    export_dir.mkdir()
    export_dir.joinpath("contacts.jsonl").write_text(
        Path("data_samples/phase_temporal_outputs/contacts.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    export_dir.joinpath("messages.jsonl").write_text(
        Path("data_samples/phase_temporal_outputs/messages.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    payload = build_nlpdata(export_dir)
    derived_dir = Path(payload["derived_dir"])

    assert payload["output_row_counts"]["phases"] == 2
    assert payload["output_row_counts"]["phase_pair_summaries"] >= 1
    assert payload["quality_metrics"]["suppressed_phase_count"] >= 1
    assert (derived_dir / "phases.jsonl").exists()
    assert (derived_dir / "phase_central_people.jsonl").exists()
    assert (derived_dir / "phase_theme_summaries.jsonl").exists()
    assert (derived_dir / "phase_pair_summaries.jsonl").exists()
    assert (derived_dir / "phase_pair_evidence.jsonl").exists()
    assert (derived_dir / "phase_representative_interactions.jsonl").exists()
    assert (derived_dir / "phase_diagnostics.jsonl").exists()


def test_phase_output_files_round_trip_jsonl_shape(tmp_path: Path) -> None:
    from archive_graph_spacy.scripts.build_nlpdata import build_nlpdata

    export_dir = tmp_path / "phase_temporal_outputs"
    export_dir.mkdir()
    export_dir.joinpath("contacts.jsonl").write_text(
        Path("data_samples/phase_temporal_outputs/contacts.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    export_dir.joinpath("messages.jsonl").write_text(
        Path("data_samples/phase_temporal_outputs/messages.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    payload = build_nlpdata(export_dir)
    derived_dir = Path(payload["derived_dir"])
    rows = [
        json.loads(line)
        for line in (derived_dir / "phase_pair_summaries.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert rows
    assert {"phase_id", "pair_id", "activity_score"}.issubset(rows[0])


def test_phase_segmentation_normalizes_mixed_timezone_timestamps() -> None:
    contacts = (
        Contact(person_id="p-alice", display_name="Alice", emails=("alice@example.com",), entity_type="person"),
        Contact(person_id="p-bob", display_name="Bob", emails=("bob@example.com",), entity_type="person"),
    )
    messages = (
        Message(
            message_id="m-1",
            source="email",
            sender="alice@example.com",
            recipients=("bob@example.com",),
            subject="First",
            body="One",
            timestamp=datetime(2024, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=-5))),
        ),
        Message(
            message_id="m-2",
            source="email",
            sender="bob@example.com",
            recipients=("alice@example.com",),
            subject="Second",
            body="Two",
            timestamp=datetime(2024, 1, 1, 17, 30),
        ),
        Message(
            message_id="m-3",
            source="email",
            sender="alice@example.com",
            recipients=("bob@example.com",),
            subject="Third",
            body="Three",
            timestamp=datetime(2024, 3, 1, 9, 0, tzinfo=UTC),
        ),
        Message(
            message_id="m-4",
            source="email",
            sender="bob@example.com",
            recipients=("alice@example.com",),
            subject="Fourth",
            body="Four",
            timestamp=datetime(2024, 3, 1, 10, 0),
        ),
    )

    result = run_pipeline(
        SourceBundle(contacts=contacts, messages=messages),
        run_scope="mixed-timezone",
    )

    assert [row.phase_index for row in result.phases] == [1, 2]
    assert result.phases[0].start_at == "2024-01-01T12:00:00-05:00"
    assert result.phases[0].end_at == "2024-01-01T17:30:00"
    assert result.phases[1].start_at == "2024-03-01T09:00:00+00:00"
    assert any(row.result == "retained" for row in result.phase_diagnostics if row.diagnostic_type == "boundary")
