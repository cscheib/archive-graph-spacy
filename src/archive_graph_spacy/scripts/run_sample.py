"""Run the sample extraction and linking workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from archive_graph_spacy.evaluate import summarize_candidate_links
from archive_graph_spacy.extract import extract_message_mentions
from archive_graph_spacy.io import load_contacts, load_messages
from archive_graph_spacy.link import link_mentions_to_people


def main() -> int:
    message_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data_samples/sample_messages.jsonl")
    contact_path = Path("data_samples/sample_contacts.jsonl")

    contacts = load_contacts(contact_path)
    messages = load_messages(message_path)

    output = []
    for message in messages:
        mentions = extract_message_mentions(message)
        linked = link_mentions_to_people(mentions, contacts)
        output.append(
            {
                "message_id": message.message_id,
                "mentions": [mention.text for mention in mentions],
                "links": {
                    mention: [
                        {
                            "person_id": candidate.person_id,
                            "score": candidate.score,
                            "reasons": list(candidate.reasons),
                        }
                        for candidate in candidates
                    ]
                    for mention, candidates in linked.items()
                },
                "summary": summarize_candidate_links(linked),
            }
        )

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
