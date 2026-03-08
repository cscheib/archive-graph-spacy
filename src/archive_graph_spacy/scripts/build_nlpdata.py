"""Build local nlpdata artifacts from an export bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_graph_spacy.nlpdata.deploy import deploy_staged_payload
from archive_graph_spacy.nlpdata.pipeline import (
    run_pipeline,
    build_pipeline_payload,
    validate_payload_contracts,
    write_pipeline_payload,
)
from archive_graph_spacy.nlpdata.source_loader import load_source_bundle_from_databricks


def build_nlpdata_from_bundle(export_dir: Path) -> dict[str, object]:
    payload = build_pipeline_payload(export_dir)
    validate_payload_contracts(payload)
    outputs_dir = write_pipeline_payload(export_dir, payload)
    run = payload["nlp_runs"][0]
    return {
        "derived_dir": str(outputs_dir),
        "run_id": run["run_id"],
        "status": run["status"],
        "input_interaction_count": run["input_interaction_count"],
        "output_row_counts": run["output_row_counts"],
        "quality_metrics": run["quality_metrics"],
    }


def build_nlpdata(export_dir: Path) -> dict[str, object]:
    return build_nlpdata_from_bundle(export_dir)


def build_nlpdata_from_databricks(
    *,
    output_dir: Path,
    catalog: str,
    warehouse_id: str,
    profile: str | None,
    message_limit: int | None,
    people_limit: int | None,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, object]:
    bundle = load_source_bundle_from_databricks(
        catalog=catalog,
        warehouse_id=warehouse_id,
        profile=profile,
        message_limit=message_limit,
        people_limit=people_limit,
        start_date=start_date,
        end_date=end_date,
    )
    result = run_pipeline(bundle, run_scope=f"{catalog}.gold", source_catalog=catalog)
    payload = {
        "nlp_runs": [result.run.to_record()],
        "message_mentions": [row.to_record() for row in result.mentions],
        "message_person_links": [row.to_record() for row in result.person_links],
        "message_theme_tags": [row.to_record() for row in result.theme_tags],
        "message_search_docs": [row.to_record() for row in result.search_docs],
    }
    validate_payload_contracts(payload)
    outputs_dir = write_pipeline_payload(output_dir, payload)
    return {
        "derived_dir": str(outputs_dir),
        "run_id": result.run.run_id,
        "status": result.run.status,
        "input_interaction_count": result.run.input_interaction_count,
        "output_row_counts": result.run.output_row_counts,
        "quality_metrics": result.run.quality_metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_dir", nargs="?", default="data_samples")
    parser.add_argument("--source", choices=("bundle", "databricks"), default="bundle")
    parser.add_argument("--output-dir", default=None, help="Output directory for derived nlpdata rows")
    parser.add_argument("--deploy", action="store_true", help="Deploy staged outputs to Databricks")
    parser.add_argument("--profile", default=None, help="Databricks CLI profile")
    parser.add_argument("--catalog", default="personal_archive_dev", help="Target catalog")
    parser.add_argument("--schema", default="nlpdata", help="Target schema")
    parser.add_argument("--warehouse-id", default="4b799682f2bfd311", help="Databricks SQL warehouse ID")
    parser.add_argument("--message-limit", type=int, default=None, help="Optional source interaction limit")
    parser.add_argument("--people-limit", type=int, default=None, help="Optional canonical person limit")
    parser.add_argument("--start-date", default=None, help="Inclusive start date YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="Exclusive end date YYYY-MM-DD")
    parser.add_argument(
        "--keep-staged-files",
        action="store_true",
        help="Keep staged DBFS files after deployment",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    export_dir = Path(args.export_dir)
    if args.source == "bundle":
        result = build_nlpdata_from_bundle(export_dir)
    else:
        output_dir = Path(args.output_dir) if args.output_dir else export_dir
        result = build_nlpdata_from_databricks(
            output_dir=output_dir,
            catalog=args.catalog,
            warehouse_id=args.warehouse_id,
            profile=args.profile,
            message_limit=args.message_limit,
            people_limit=args.people_limit,
            start_date=args.start_date,
            end_date=args.end_date,
        )
    if args.deploy:
        result["deployment"] = deploy_staged_payload(
            Path(result["derived_dir"]),
            run_id=str(result["run_id"]),
            profile=args.profile,
            catalog=args.catalog,
            schema=args.schema,
            warehouse_id=args.warehouse_id,
            cleanup_remote=not args.keep_staged_files,
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
