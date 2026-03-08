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
