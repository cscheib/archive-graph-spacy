"""Run extraction and linking against a graph-data export directory.

[EXPERIMENTAL] This script is not the primary product path. It is retained for
ad hoc debugging only and is planned for retirement once the build_nlpdata
pipeline is confirmed as the stable replacement.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from archive_graph_spacy.evaluate import summarize_candidate_links
from archive_graph_spacy.extract import extract_message_mentions
from archive_graph_spacy.io import load_export_bundle
from archive_graph_spacy.link import link_mentions_to_people


def main() -> int:
    export_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data_exports/latest")
    contacts, messages = load_export_bundle(export_dir)

    output = []
    for message in messages:
        mentions = extract_message_mentions(message)
        linked = link_mentions_to_people(mentions, contacts)
        output.append(
            {
                "message_id": message.message_id,
                "source": message.source,
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
