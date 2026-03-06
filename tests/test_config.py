import importlib

import archive_graph_spacy.config as config


def test_get_owner_person_id_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("OWNER_PERSON_ID", "p-owner")

    importlib.reload(config)

    assert config.get_owner_person_id() == "p-owner"


def test_get_owner_person_id_returns_none_when_blank(monkeypatch) -> None:
    monkeypatch.setenv("OWNER_PERSON_ID", "")

    importlib.reload(config)

    assert config.get_owner_person_id() is None
