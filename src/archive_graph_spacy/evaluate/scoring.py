"""Simple summaries for experiment results."""

from __future__ import annotations

from archive_graph_spacy.models import LinkCandidate


def summarize_candidate_links(results: dict[str, list[LinkCandidate]]) -> dict[str, int]:
    linked_mentions = sum(1 for candidates in results.values() if candidates)
    total_candidates = sum(len(candidates) for candidates in results.values())
    return {
        "linked_mentions": linked_mentions,
        "total_candidates": total_candidates,
    }
