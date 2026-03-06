from pathlib import Path

from archive_graph_spacy.webapp import (
    discover_bundles,
    render_index_html,
    render_message_page,
    render_person_page,
)


def test_discover_bundles_finds_data_samples_and_exports(tmp_path: Path) -> None:
    samples = tmp_path / "data_samples"
    samples.mkdir()
    (samples / "sample_contacts.jsonl").write_text("{}\n", encoding="utf-8")
    exports = tmp_path / "data_exports" / "bundle-a"
    exports.mkdir(parents=True)
    (exports / "contacts.jsonl").write_text("{}\n", encoding="utf-8")

    bundles = discover_bundles(tmp_path)

    assert samples in bundles
    assert exports in bundles


def test_render_index_html_includes_bundle_and_person_picker(tmp_path: Path) -> None:
    bundle = tmp_path / "data_exports" / "bundle-a"
    derived = bundle / "derived"
    derived.mkdir(parents=True)
    (bundle / "contacts.jsonl").write_text(
        '{"person_id":"p-1","display_name":"Alice Example","entity_type":"person"}\n',
        encoding="utf-8",
    )
    (derived / "person_person_edges.jsonl").write_text(
        (
            '{"person_a_id":"p-1","person_a_name":"Alice Example","person_a_type":"person",'
            '"person_b_id":"p-2","person_b_name":"Bob Example","person_b_type":"person",'
            '"message_count":2,"mention_count":1,"co_participant_count":2,"confidence":1.0,'
            '"strongest_relationship_type":"co_participant","strongest_message_id":"m-1"}\n'
        ),
        encoding="utf-8",
    )

    html = render_index_html(tmp_path, bundle, "Refreshed")

    assert "bundle-a" in html
    assert "Alice Example" in html
    assert "Refreshed" in html
    assert "Open Full Graph" in html
    assert "Interaction Explorer" in html


def test_render_message_page_highlights_mentions(tmp_path: Path) -> None:
    bundle = tmp_path / "data_exports" / "bundle-a"
    bundle.mkdir(parents=True)
    (bundle / "contacts.jsonl").write_text(
        (
            '{"person_id":"p-alice","display_name":"Alice Example","emails":["alice@example.com"],'
            '"entity_type":"person"}\n'
            '{"person_id":"p-bob","display_name":"Bob Example","emails":["bob@example.com"],'
            '"phones":["+15550001002"],"entity_type":"person"}\n'
        ),
        encoding="utf-8",
    )
    (bundle / "messages.jsonl").write_text(
        (
            '{"message_id":"m-1","source":"email","sender":"alice@example.com",'
            '"recipients":["bob@example.com"],"subject":"Dinner","body":"Call Bob Example at +1 555 000 1002","timestamp":"2026-03-06T12:00:00"}\n'
        ),
        encoding="utf-8",
    )

    html = render_message_page(bundle, "m-1")

    assert "Interaction Explorer" in html
    assert "Bob Example" in html
    assert "<mark" in html
    assert "Candidates" in html


def test_render_person_page_lists_message_links(tmp_path: Path) -> None:
    bundle = tmp_path / "data_exports" / "bundle-a"
    derived = bundle / "derived"
    derived.mkdir(parents=True)
    (derived / "person_message_edges.jsonl").write_text(
        (
            '{"person_id":"p-1","person_name":"Alice Example","person_type":"person",'
            '"message_id":"m-1","role":"recipient","strongest_evidence_type":"header_email",'
            '"strongest_evidence_value":"alice@example.com","confidence":1.0,"source":"email"}\n'
        ),
        encoding="utf-8",
    )

    html = render_person_page(bundle, "p-1")

    assert "Person Explorer" in html
    assert "Alice Example" in html
    assert "m-1" in html
