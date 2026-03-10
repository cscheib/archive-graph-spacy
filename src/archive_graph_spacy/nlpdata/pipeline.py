"""Pipeline orchestration for local nlpdata derivation."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

from .contracts import TABLE_CONTRACTS
from .models import PipelineResult, SourceBundle
from .person_links import apply_reviewed_feedback, derive_candidate_assertions, derive_person_links
from .runs import build_refresh_run, meets_runtime_goal, new_run_id, utc_now
from .search_docs import build_search_documents
from .source_loader import load_source_bundle
from .themes import derive_theme_tags
from archive_graph_spacy.edges.person_person import build_nlpdata_person_person_outputs


def _rebuild_candidate_summary(
    original_summary: object,
    *,
    candidate_assertions: tuple,
    reviewed_effects: tuple,
):
    candidate_counts: dict[str, int] = defaultdict(int)
    for candidate in candidate_assertions:
        candidate_counts[candidate.assertion_type] += 1
    reviewed_effect_counts: dict[str, int] = defaultdict(int)
    for effect in reviewed_effects:
        reviewed_effect_counts[effect.result] += 1
    return original_summary.__class__(
        run_id=original_summary.run_id,
        generation_scope=original_summary.generation_scope,
        emitted_candidate_count=len(candidate_assertions),
        candidate_counts_by_type=dict(candidate_counts),
        suppressed_counts=original_summary.suppressed_counts,
        example_candidate_ids=tuple(candidate.candidate_assertion_id for candidate in candidate_assertions[:5]),
        generated_at=original_summary.generated_at,
        reviewed_effect_counts=dict(reviewed_effect_counts),
    )


def run_pipeline(
    bundle: SourceBundle,
    *,
    run_scope: str,
    source_catalog: str = "personal_archive_dev",
) -> PipelineResult:
    run_id = new_run_id()
    started_at = utc_now()
    started_timer = time.perf_counter()

    mentions, person_links, person_suppressed = derive_person_links(bundle.messages, bundle.contacts, run_id)
    candidate_assertions, candidate_summary = derive_candidate_assertions(
        bundle.messages,
        bundle.contacts,
        run_id,
        run_scope,
    )
    candidate_assertions, reviewed_effects, reviewed_links = apply_reviewed_feedback(
        run_id=run_id,
        contacts=bundle.contacts,
        candidate_assertions=candidate_assertions,
        reviewed_assertions=bundle.reviewed_assertions,
        review_assertion_decisions=bundle.review_assertion_decisions,
    )
    link_index = {(link.message_id, link.person_id, link.role): link for link in person_links}
    for link in reviewed_links:
        link_index[(link.message_id, link.person_id, link.role)] = link
    person_links = tuple(link_index.values())
    candidate_summary = _rebuild_candidate_summary(
        candidate_summary,
        candidate_assertions=candidate_assertions,
        reviewed_effects=reviewed_effects,
    )
    theme_tags, theme_suppressed = derive_theme_tags(bundle.messages, run_id)
    search_docs, search_suppressed = build_search_documents(bundle.messages, person_links, theme_tags, run_id)
    person_person_edges, person_person_edge_evidence = build_nlpdata_person_person_outputs(
        person_links,
        run_id=run_id,
        generation_scope=run_scope,
    )

    duration_seconds = time.perf_counter() - started_timer
    completed_at = utc_now()
    output_row_counts = {
        "message_mentions": len(mentions),
        "message_person_links": len(person_links),
        "candidate_assertions": len(candidate_assertions),
        "reviewed_effects": len(reviewed_effects),
        "person_person_edges": len(person_person_edges),
        "person_person_edge_evidence": len(person_person_edge_evidence),
        "message_theme_tags": len(theme_tags),
        "message_search_docs": len(search_docs),
    }
    quality_metrics: dict[str, int | float | bool] = {
        **person_suppressed,
        **candidate_summary.suppressed_counts,
        **theme_suppressed,
        **search_suppressed,
        "runtime_seconds": round(duration_seconds, 6),
        "meets_runtime_goal": meets_runtime_goal(len(bundle.messages), duration_seconds),
    }
    run = build_refresh_run(
        run_id=run_id,
        run_scope=run_scope,
        source_catalog=source_catalog,
        started_at=started_at,
        completed_at=completed_at,
        input_interaction_count=len(bundle.messages),
        output_row_counts=output_row_counts,
        quality_metrics=quality_metrics,
    )
    return PipelineResult(
        run=run,
        mentions=mentions,
        person_links=person_links,
        candidate_assertions=candidate_assertions,
        candidate_summary=candidate_summary,
        reviewed_effects=reviewed_effects,
        theme_tags=theme_tags,
        search_docs=search_docs,
        person_person_edges=person_person_edges,
        person_person_edge_evidence=person_person_edge_evidence,
        suppressed_counts={
            key: value
            for key, value in quality_metrics.items()
            if key not in {"runtime_seconds", "meets_runtime_goal"}
        },
    )


def build_pipeline_payload(export_dir: str | Path) -> dict[str, object]:
    bundle = load_source_bundle(export_dir)
    result = run_pipeline(bundle, run_scope=str(export_dir))
    return {
        "nlp_runs": [result.run.to_record()],
        "message_mentions": [row.to_record() for row in result.mentions],
        "message_person_links": [row.to_record() for row in result.person_links],
        "candidate_assertions": [row.to_record() for row in result.candidate_assertions],
        "message_theme_tags": [row.to_record() for row in result.theme_tags],
        "message_search_docs": [row.to_record() for row in result.search_docs],
        "candidate_assertions_summary": result.candidate_summary.to_record(),
        "reviewed_effects": [row.to_record() for row in result.reviewed_effects],
        "person_person_edges": [row.to_record() for row in result.person_person_edges],
        "person_person_edge_evidence": [row.to_record() for row in result.person_person_edge_evidence],
    }


def write_pipeline_payload(export_dir: str | Path, payload: dict[str, object]) -> Path:
    base = Path(export_dir) / "derived" / "nlpdata"
    base.mkdir(parents=True, exist_ok=True)
    for artifact_name, rows in payload.items():
        if artifact_name == "candidate_assertions_summary":
            path = base / f"{artifact_name}.json"
            with path.open("w", encoding="utf-8") as handle:
                json.dump(rows, handle, indent=2, sort_keys=True)
                handle.write("\n")
            continue

        path = base / f"{artifact_name}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
    return base


def validate_payload_contracts(payload: dict[str, object]) -> None:
    for artifact_name, required_columns in TABLE_CONTRACTS.items():
        rows = payload.get(artifact_name, [])
        if artifact_name == "candidate_assertions_summary":
            if not isinstance(rows, dict):
                raise ValueError(f"{artifact_name} payload must be a dict")
            missing = [column for column in required_columns if column not in rows]
            if missing:
                raise ValueError(f"{artifact_name} payload missing columns: {missing}")
            continue

        if not isinstance(rows, list):
            raise ValueError(f"{artifact_name} payload must be a list of row dicts")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"{artifact_name} row must be a dict")
            missing = [column for column in required_columns if column not in row]
            if missing:
                raise ValueError(f"{artifact_name} row missing columns: {missing}")
