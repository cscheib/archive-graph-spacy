# Deprecated Roadmap Document

This file is no longer the active source of truth for roadmap planning.

## Source Of Truth

Use the GitHub Project instead:

- [Social Graph Analysis Project](https://github.com/users/cscheib/projects/1)

That project now owns the active planning backlog across:

- `cscheib/archive-graph-data`
- `cscheib/archive-graph-spacy`

## What This Means

- roadmap sequencing should be maintained in the GitHub Project
- planning details should live in linked GitHub issues
- the shared cross-repo contract is published in
  [specs/002-formalize-cross-repo-contract/spec.md](../specs/002-formalize-cross-repo-contract/spec.md)
  and [docs/adr/002-cross-repo-contract.md](adr/002-cross-repo-contract.md)
- the reviewed-assertions lifecycle model is published in
  [specs/003-reviewed-assertions-pipeline/spec.md](../specs/003-reviewed-assertions-pipeline/spec.md),
  [specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md](../specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md),
  and [docs/adr/003-reviewed-assertions-promotion-model.md](adr/003-reviewed-assertions-promotion-model.md)
- the first implemented candidate-generation surface is published in
  [specs/004-candidate-assertions/spec.md](../specs/004-candidate-assertions/spec.md)
  and [specs/004-candidate-assertions/contracts/candidate-assertions-surface.md](../specs/004-candidate-assertions/contracts/candidate-assertions-surface.md)
- the hardened bounded publish model is published in
  [specs/005-nlpdata-publish-hardening/spec.md](../specs/005-nlpdata-publish-hardening/spec.md),
  [specs/005-nlpdata-publish-hardening/contracts/bounded-publish-semantics.md](../specs/005-nlpdata-publish-hardening/contracts/bounded-publish-semantics.md),
  and [docs/adr/004-nlpdata-publish-semantics.md](adr/004-nlpdata-publish-semantics.md)
- this file is retained only as a pointer for future readers

## Current Planning Focus

The current early-stage execution focus is:

1. cross-repo contract and reviewed-assertions model
2. candidate-generation consumption and review UI in `archive-graph-data`
3. follow-on relationship and diagnostics surfaces
4. downstream review consumption and operational polish

## Planned Cleanup Phase — Retiring Superseded Experimental Surfaces

A later cleanup phase is explicitly part of the roadmap. It covers retiring the
experimental or AI-derived surfaces that are superseded once the `nlpdata`
pipeline and reviewed-assertions path are confirmed stable. This includes:

- `scripts/run_export.py` — superseded by the `build_nlpdata` pipeline
- `scripts/run_sample.py` — superseded by `build_nlpdata data_samples` and
  the automated test suite
- `webapp.py` / `scripts/webapp.py` — superseded by downstream review UI in
  `archive-graph-data`; retained as a local exploration tool only
- Direct use of `extract`/`link`/`evaluate` modules outside the pipeline
  boundary — superseded by `nlpdata` contract-enforced derivation

Retirement is conditioned on confirmed deterministic replacement. No experimental
surface will be removed until a stable, tested replacement is verified in the
supported path.

The deprecation inventory and conditions are published here:

- [Spec 008: Deprecate Experimental Surfaces](../specs/008-deprecate-experimental-surfaces/spec.md)
