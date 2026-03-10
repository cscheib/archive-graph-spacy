from types import SimpleNamespace

import pytest

from archive_graph_spacy.nlpdata.source_loader import load_source_bundle_from_databricks


class FakeSqlClient:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []

    def fetch_all(self, statement: str):
        self.queries.append(statement)
        if "FROM `personal_archive_dev`.gold.interactions" in statement:
            return self.rows["messages"]
        if "FROM `personal_archive_dev`.gold.persons" in statement:
            return self.rows["contacts"]
        if "FROM `personal_archive_dev`.memory.reviewed_assertions" in statement:
            return self.rows.get("reviewed_assertions", [])
        if "FROM `personal_archive_dev`.memory.review_assertion_decisions" in statement:
            return self.rows.get("review_assertion_decisions", [])
        raise AssertionError(f"Unexpected query: {statement}")


def test_load_source_bundle_from_databricks_maps_rows(monkeypatch) -> None:
    rows = {
        "contacts": [
            {
                "person_id": "p-alice",
                "display_name": "Alice Example",
                "emails": ["alice@example.com"],
                "phones": ["+15550001001"],
                "photo_url": None,
                "entity_type": "person",
            }
        ],
        "messages": [
            {
                "message_id": "m-001",
                "source": "email",
                "sender": "alice@example.com",
                "recipients": "bob@example.com",
                "subject": "Trip",
                "body": "Flight hotel trip",
                "timestamp": "2026-03-06T10:00:00",
                "interaction_type": "email",
            }
        ],
        "reviewed_assertions": [
            {
                "candidate_assertion_id": "legacy-relay-bob",
                "assertion_type": "relay_sender_identity",
                "subject_canonical_id": "m-relay-bob",
                "proposed_claim": "relay sender relay+bob@relay.example.com maps to p-bob",
                "current_review_state": "accepted",
            }
        ],
        "review_assertion_decisions": [
            {
                "candidate_assertion_id": "legacy-relay-bob",
                "decision_state": "accepted",
            }
        ],
    }
    fake_client = FakeSqlClient(rows)
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.source_loader.get_workspace_client",
        lambda profile=None: SimpleNamespace(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.source_loader.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: fake_client,
    )

    bundle = load_source_bundle_from_databricks(
        catalog="personal_archive_dev",
        warehouse_id="warehouse-1",
        profile="dev-profile",
        message_limit=100,
        people_limit=200,
        start_date="2020-01-01",
        end_date="2026-01-01",
    )

    assert bundle.contacts[0].person_id == "p-alice"
    assert bundle.messages[0].message_id == "m-001"
    assert bundle.messages[0].recipients == ("bob@example.com",)
    assert bundle.reviewed_assertions[0]["candidate_assertion_id"] == "legacy-relay-bob"
    assert bundle.review_assertion_decisions[0]["decision_state"] == "accepted"
    assert any("LIMIT 100" in query for query in fake_client.queries)
    assert any("LIMIT 200" in query for query in fake_client.queries)


def test_load_source_bundle_from_databricks_rejects_invalid_catalog(monkeypatch) -> None:
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.source_loader.get_workspace_client",
        lambda profile=None: SimpleNamespace(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.source_loader.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: FakeSqlClient({"messages": [], "contacts": []}),
    )

    with pytest.raises(ValueError, match="Invalid SQL identifier"):
        load_source_bundle_from_databricks(catalog="personal_archive_dev;DROP TABLE gold.interactions")
