import json

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
