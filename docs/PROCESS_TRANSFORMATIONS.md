# Process Transformations

This document complements the contract/spec material in `specs/` and `docs/adr/`.

Those documents answer: "what is the output surface and ownership boundary?"

This document answers: "what actually happens to the data inside each primary process?"

## Transformation Legend

- `Load`: read bundle rows or Databricks tables into the source bundle
- `Extract`: derive mentions, tokens, spans, or evidence from raw message text
- `Link`: map a sender, recipient, or mention to a canonical person
- `Suppress`: deliberately drop noisy or low-confidence derivations
- `Replay`: re-apply prior human review to regenerated candidates
- `Project`: reshape link data into search, edge, or review surfaces
- `Segment`: split the accumulated message stream into bounded temporal phases
- `Stage`: upload local artifacts for publish
- `Finalize`: deactivate prior current rows and activate the new run’s staged rows

## Primary Surfaces

```mermaid
flowchart TB
    A["build_nlpdata.py<br/>local or Databricks source loader"] --> B["run_pipeline()<br/>mentions + links + review replay + themes + search"]
    B --> C["derived/nlpdata/*.jsonl|json"]
    C --> D["deploy_staged_payload()<br/>bounded publish to Databricks"]

    E["01_nlpdata_refresh.py"] --> B
    B --> F["personal_archive_dev.nlpdata current-state rows"]
    F --> G["02_nlpdata_phase_refresh.py<br/>global phase rebuild"]
    G --> H["personal_archive_dev.nlpdata phase tables"]

    I["build_edges.py"] --> J["derived/*.jsonl edge tables"]
    J --> K["query_edges.py / visualize_ego.py / visualize_graph.py"]
```

## Data Families

```mermaid
flowchart LR
    subgraph Source["Source bundle"]
        S1["contacts"]
        S2["messages"]
        S3["reviewed_assertions"]
        S4["review_assertion_decisions"]
    end

    subgraph MessageFlow["Message-centric derivation"]
        M1["message_mentions"]
        M2["message_person_links"]
        M3["candidate_assertions + reviewed_effects"]
        M4["message_theme_tags"]
        M5["message_search_docs"]
    end

    subgraph GraphFlow["Relationship derivation"]
        G1["person_person_edges"]
        G2["person_person_edge_evidence"]
        G3["phases + phase_* outputs<br/>(second pass over accumulated current rows)"]
    end

    subgraph Publish["Publish state"]
        P1["nlp_runs"]
        P2["current-state nlpdata tables"]
    end

    S1 --> M2
    S2 --> M1 --> M2 --> M3 --> M4 --> M5
    S3 --> M3
    S4 --> M3
    M2 --> G1
    G1 --> G2 --> G3
    M4 --> G3
    M2 --> G3
    M1 --> P1
    M2 --> P1
    M3 --> P1
    M4 --> P1
    M5 --> P1
    G1 --> P1
    G2 --> P1
    G3 --> P1
    P1 --> P2
```

## 1. Source Loading

Goal: turn either an export bundle or live Databricks tables into one normalized `SourceBundle`.

```mermaid
flowchart TB
    A["Local export bundle"] --> C["load_source_bundle()"]
    B["Databricks gold/memory tables"] --> D["load_source_bundle_from_databricks()"]
    C --> E["SourceBundle"]
    D --> E
```

### What actually happens

- Local mode reads:
  - `contacts.jsonl`
  - `messages.jsonl`
  - optional `reviewed_assertions.jsonl`
  - optional `review_assertion_decisions.jsonl`
- Databricks mode reads:
  - canonical people from `gold.persons`
  - message-like interactions from `gold.interactions`
  - optional reviewed feedback from `memory.reviewed_assertions` and `memory.review_assertion_decisions`
- Contacts are normalized into a compact person shape:
  - `person_id`
  - display name
  - emails
  - phones
  - photo URL
  - effective entity type
- Messages are normalized into a compact interaction shape:
  - message id
  - sender
  - recipients
  - subject
  - body
  - timestamp
  - interaction type
- Reviewed assertions are scoped to the current message set, plus pair-scoped relationship assertions that reference relevant messages.

## 2. Mention Extraction

Goal: turn message text into candidate spans with provenance.

```mermaid
flowchart TB
    A["subject + body"] --> B["Regex pass<br/>emails + phones"]
    A --> C["spaCy NER<br/>PERSON spans"]
    A --> D["Heuristic title-case spans<br/>multi-token + single-token"]
    B --> E["Normalize / drop greeting noise"]
    C --> E
    D --> E
    E --> F["Deduplicate spans"]
    F --> G["message_mentions"]
```

### What actually happens

- The pipeline combines `subject` and `body` into one extraction surface.
- It extracts:
  - emails via regex
  - phones via regex
  - `PERSON` spans via spaCy
  - title-cased heuristic person candidates when the NER model misses them
- Greeting/noise spans like `Hello`, `Hi`, or other low-value tokens are stripped or dropped.
- Multi-token person spans are preferred over nested single-token spans.
- The output is a deduplicated set of `InteractionMention` rows per message, each with:
  - source type
  - span offsets
  - confidence
  - stable mention id

## 3. Person Linking

Goal: resolve message participants and text mentions to canonical people.

```mermaid
flowchart TB
    A["message headers"] --> B["Explicit participants<br/>sender + recipients"]
    C["message_mentions"] --> D["Mention-to-person candidates"]
    E["contacts"] --> D
    B --> F["DerivedLinkContext"]
    D --> F
    F --> G["Publish explicit links"]
    F --> H["Publish inferred mention links if confidence >= threshold"]
    F --> I["Suppress unresolved / low-confidence / non-person matches"]
    G --> J["message_person_links"]
    H --> J
```

### What actually happens

- Header-level resolution identifies explicit participants from sender and recipient emails.
- Mention-level resolution uses the canonical person set and link scoring from the linking module.
- Explicit participants bias mention resolution so the linker prefers people already on the message.
- `derive_person_links()` emits:
  - explicit sender links
  - explicit recipient links
  - inferred `mentioned` links when the best candidate clears the minimum threshold and is a `person`
- Everything else becomes suppression or unresolved quality metrics rather than published links.

## 4. Candidate Assertion Generation

Goal: create reviewable, pre-canonical assertions when the pipeline sees a risky or ambiguous situation.

```mermaid
flowchart TB
    A["DerivedLinkContext"] --> B["Relay sender heuristic"]
    A --> C["Single-token ambiguity heuristic"]
    A --> D["Direct vs indirect pair-evidence heuristic"]
    B --> E["relay_sender_identity"]
    C --> F["person_link_disambiguation"]
    D --> G["relationship_evidence_review"]
    H["system-generated message?"] --> I["suppress review candidate"]
```

### What actually happens

- The pipeline suppresses review candidates for system-generated messages.
- It emits `relay_sender_identity` when:
  - sender looks relay-like
  - sender is unresolved
  - there is exactly one strong supporting inferred person link
- It emits `person_link_disambiguation` when:
  - a single-token person mention has multiple plausible people
  - there is no clear winner
  - the ambiguity is considered worth asking a human
- It emits `relationship_evidence_review` when the same pair has both:
  - direct evidence from explicit co-participation
  - indirect evidence from mention-based inference
- The output is still non-canonical. These are review prompts, not accepted facts.

## 5. Reviewed Feedback Replay

Goal: let prior human review change what this run publishes.

```mermaid
flowchart TB
    A["candidate_assertions"] --> B["Match reviewed inputs by candidate id or semantic replay key"]
    C["reviewed_assertions + review decisions"] --> B
    B --> D["accepted"]
    B --> E["rejected / superseded"]
    B --> F["ignored / conflicted / skipped"]
    D --> G["emit reviewed links where applicable"]
    E --> H["suppress candidate re-emission"]
    F --> I["record reviewed_effects only"]
```

### What actually happens

- Reviewed rows from `graph-data` are normalized into one replay stream.
- Each reviewed item is matched back to regenerated candidates by:
  - exact candidate id, or
  - semantic replay key for rerun stability
- Accepted decisions can materialize new `reviewed` person-message links, especially for:
  - relay sender identity
  - person disambiguation
- Rejected or superseded decisions suppress those candidates from reappearing in the queue.
- Every replay decision produces a `reviewed_effects` audit row so the run records what human feedback changed.

## 6. Theme Tagging

Goal: derive a small deterministic topic layer for non-system messages.

```mermaid
flowchart TB
    A["messages"] --> B["Skip system-generated messages"]
    B --> C["Keyword/theme rules"]
    C --> D["Confidence threshold"]
    D --> E["message_theme_tags"]
```

### What actually happens

- Messages from obvious notification/system senders are skipped.
- Rule-based theme matching looks for curated keywords across subject and body.
- Only tags that cross the minimum confidence threshold are emitted.
- Theme outputs are deterministic and intentionally narrow rather than LLM-generated.

## 7. Search Document Projection

Goal: compress message, link, and theme outputs into a search-friendly row.

```mermaid
flowchart TB
    A["messages"] --> D["build_search_documents()"]
    B["message_person_links"] --> D
    C["message_theme_tags"] --> D
    D --> E["tokenize subject/body"]
    D --> F["attach linked people + names"]
    D --> G["split explicit vs inferred person facets"]
    D --> H["derive time facets"]
    E --> I["message_search_docs"]
    F --> I
    G --> I
    H --> I
```

### What actually happens

- System-generated messages are dropped from the search surface.
- Messages with no surviving links and no surviving themes are suppressed as empty search docs.
- The projection stores:
  - tokenized subject terms
  - tokenized body terms
  - linked person ids and names
  - explicit vs inferred person facets
  - theme labels
  - time facets like year and year-month
- The pipeline also flags messages where all derivation remained unresolved.

## 8. Person-Person Edge Projection

Goal: turn person-message links into pairwise relationship evidence.

```mermaid
flowchart TB
    A["message_person_links"] --> B["Explicit co-participation => direct evidence"]
    A --> C["Explicit participant + mentioned person => indirect evidence"]
    B --> D["pair evidence rows"]
    C --> D
    D --> E["rank and cap evidence per pair"]
    E --> F["person_person_edge_evidence"]
    E --> G["aggregate pair summaries"]
    G --> H["person_person_edges"]
```

### What actually happens

- Two explicit people on the same message create direct participation evidence.
- An explicit participant plus an inferred mention of someone else creates mention-based pair evidence.
- Evidence rows are deduplicated, ranked, and capped per pair.
- Pair summaries publish:
  - pair id
  - strongest relationship signal
  - direct evidence count
  - indirect evidence count
  - strongest evidence ref

## 9. Phase Segmentation and Temporal Outputs

Goal: turn the accumulated message stream into bounded temporal phases with diagnostics.

```mermaid
flowchart TB
    A["timestamped messages"] --> B["Sort by timestamp"]
    B --> C["Gap analysis"]
    C --> D[">=45d gap => retain boundary"]
    C --> E[">=14d and <45d => merge boundary"]
    D --> F["segments"]
    E --> F
    F --> G["suppress weak segments"]
    G --> H["phase records"]
    H --> I["central people / theme summaries / pair summaries"]
    H --> J["representative interactions"]
    H --> K["phase diagnostics"]
```

### What actually happens

- Phase analysis now runs after the batch-oriented `nlpdata` writes complete.
- It reads the accumulated current-state message, link, theme, and pair-evidence
  rows, then rebuilds all phase tables in one global pass.
- Only timestamped messages participate in phases.
- Messages are sorted chronologically and split on large gaps.
- Current defaults:
  - `>= 45` days keeps a boundary
  - `>= 14` and `< 45` days records a merged boundary but does not split
- Tiny segments are suppressed instead of published as weak phases.
- Published phase outputs include:
  - `phases`
  - `phase_central_people`
  - `phase_theme_summaries`
  - `phase_pair_summaries`
  - `phase_pair_evidence`
  - `phase_representative_interactions`
  - `phase_diagnostics`

## 10. Run Metadata and Quality Metrics

Goal: record not just rows emitted, but what got suppressed and whether the run was healthy.

```mermaid
flowchart TB
    A["mentions / links / candidates / themes / search / phases"] --> B["count outputs"]
    A --> C["collect suppression metrics"]
    B --> D["runtime + throughput goal check"]
    C --> E["quality_metrics"]
    D --> E
    E --> F["nlp_runs"]
```

### What actually happens

- The pipeline records counts for every emitted table.
- It also records suppression and diagnostic counters from each stage.
- Runtime is checked against a throughput target rather than just absolute duration.
- A single `RefreshRun` row becomes the run-level audit record for the whole derivation.

## 11. Local Build Surface: `build_nlpdata.py`

Goal: run the full derivation locally or against live Databricks data, then write staged artifacts.

```mermaid
flowchart TB
    A["bundle mode"] --> C["build_pipeline_payload()"]
    B["databricks mode"] --> D["load_source_bundle_from_databricks() -> run_pipeline()"]
    C --> E["validate payload contracts"]
    D --> E
    E --> F["write derived/nlpdata/*.jsonl|json"]
    F --> G["optional deploy_staged_payload()"]
```

### What actually happens

- Bundle mode is the local deterministic path over exported files.
- Databricks mode pulls live source data, runs the same in-memory pipeline, then writes local staged artifacts.
- The payload is contract-validated before writing.
- `candidate_assertions_summary` is written as `.json`; all other artifacts are `.jsonl`.
- Optional `--deploy` publishes those staged files immediately after building them.

## 12. Databricks Notebook Surface: `01_nlpdata_refresh.py`

Goal: run the batch-oriented derivation inside Databricks and publish directly.

```mermaid
flowchart TB
    A["gold.persons + gold.interactions"] --> B["source_bundle_from_rows()"]
    A --> C["optional reviewed inputs"]
    B --> D["run_pipeline()"]
    C --> D
    D --> E["create temp views over result rows"]
    E --> F["insert non-phase nlpdata tables"]
    F --> G["current-state finalization for bounded tables"]
    G --> H["optional chain to 02_nlpdata_phase_refresh.py"]
```

### What actually happens

- The notebook reconstructs the in-memory source bundle from Spark SQL rows.
- It runs the same `run_pipeline()` logic as the CLI path, but defers phase
  outputs for bounded refresh windows.
- It creates temp views for each result table, including the singleton `nlp_runs` row.
- For candidate assertions, it first deletes matching existing candidate ids to avoid rerun duplication.
- For current-state tables, it deactivates prior rows for the same identity set and then activates the staged rows for the new run.
- Unbounded refreshes chain into `02_nlpdata_phase_refresh.py` after the non-phase writes complete.

## 13. Databricks Notebook Surface: `02_nlpdata_phase_refresh.py`

Goal: rebuild `phases` and `phase_*` tables after batch accumulation.

- Loads the full eligible interaction stream from `gold.interactions`.
- Loads current `message_person_links`, `message_theme_tags`, and
  `person_person_edges` from `nlpdata`.
- Deduplicates `person_person_edge_evidence` against the current pair set.
- Runs the global phase refresh pass.
- Deactivates prior current phase rows by generation scope, then inserts the new
  phase rows.

## 14. Publish / Deploy Surface

Goal: stage local artifacts to DBFS and apply bounded publish semantics safely.

```mermaid
flowchart TB
    A["derived/nlpdata local files"] --> B["stage_payload_directory()"]
    B --> C["create schemas / tables / missing columns"]
    C --> D["insert staged rows as non-current"]
    D --> E["collect bounded publish scope"]
    E --> F["overlap check"]
    F -->|safe| G["deactivate prior current rows in scope"]
    G --> H["activate this run's staged rows"]
    F -->|overlap conflict| I["fail with publish diagnostics"]
    H --> J["persist publish_diagnostics onto nlp_runs"]
```

### What actually happens

- Every artifact is uploaded to a remote staged directory first.
- The deploy path creates missing schemas/tables and adds missing columns to match the current contract.
- Current-state tables are inserted as `is_current = false` first.
- The deploy path computes bounded scope:
  - affected messages
  - affected identities
  - affected tables
- If the new scope overlaps a currently active unrelated scope, the publish fails fast instead of corrupting current-state rows.
- Safe publishes then:
  - deactivate prior current rows in scope
  - activate the staged rows for this run
- Diagnostics are written back to `nlp_runs.publish_diagnostics`.

## 15. Local Edge Analysis Path

Goal: provide a simpler, non-`nlpdata` graph-analysis surface over export bundles.

```mermaid
flowchart TB
    A["contacts + messages"] --> B["build_person_message_edge_evidence()"]
    B --> C["aggregate person-message edges"]
    C --> D["build person-person evidence"]
    D --> E["aggregate person-person edges"]
    E --> F["derived/*.jsonl"]
    F --> G["query_edges.py"]
    F --> H["visualize_ego.py / visualize_graph.py"]
```

### What actually happens

- `build_edges.py` is the lighter-weight local graph path.
- It derives:
  - person-message evidence
  - aggregated person-message edges
  - person-person evidence
  - aggregated person-person edges
- `query_edges.py` runs preset DuckDB queries over those JSONL tables.
- `visualize_ego.py` and `visualize_graph.py` render HTML network views on top of the derived edge tables.

## Quick Reading Guide

If you want to understand one specific behavior quickly:

- Mention extraction and ambiguity:
  - `mentions.py`
  - `person_links.py`
- Candidate review queue and replay:
  - `person_links.py`
- Search surface:
  - `themes.py`
  - `search_docs.py`
- Temporal segmentation:
  - `pipeline.py`
- Publish semantics:
  - `deploy.py`
  - `01_nlpdata_refresh.py`
- Local graph exploration path:
  - `build_edges.py`
  - `edges/person_message.py`
  - `edges/person_person.py`
