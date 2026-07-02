---
name: reuse-map
description: Cross-skill wiring and shared sub-skill references for the business-operations cluster.
---

## Purpose
This map documents how `recruitment-process-audit` (cluster: `business-operations`, idea #103)
shares and reuses sub-skills with sibling skills in the same cluster, and how its standardized
scoring output schema (`skills/scoring-schema.json`) is the cross-skill contract. It satisfies
Phase 5: at least one sub-skill is reused **from** this skill **for** a sibling cluster skill, and
this skill reuses a cluster-shared sub-skill in turn.

## Cluster: `business-operations`
Sibling skills in this cluster operate on a common pattern: stakeholder-aware, evidence-grounded
analysis of a business artifact with a transparent, dimension-based score and a measurable roadmap.
Two capabilities are naturally cluster-shared:

1. **`sub-stakeholder-mapper`** - generic stakeholder (interest x influence) mapping. Domain-neutral;
   any business-operations skill that must "account for every party who must approve, execute, or be
   affected by it" reuses this sub-skill verbatim.
2. **`sub-scoring-engine` + `skills/scoring-schema.json`** - generic multi-dimensional scoring with
   per-dimension evidence, a weighted total, ranked weaknesses, and a measurable roadmap. The schema
   standardizes the output so scores are comparable across skills and benchmark/improvement loops are
   portable.

## Reuse table

| Sub-skill / artifact | Originating skill | Reused BY (sibling) | How it is reused |
|----------------------|-------------------|---------------------|------------------|
| `sub-stakeholder-mapper` | `recruitment-process-audit` | any `business-operations` skill (e.g. vendor-selection-audit, process-improvement-audit) | Invoked as the first harness step; identical inputs/outputs/gate; domain context supplied by the calling harness. |
| `sub-scoring-engine` | `recruitment-process-audit` | any `business-operations` skill that scores an artifact | Same workflow; dimension set is supplied by the calling skill; output MUST conform to `scoring-schema.json`. |
| `skills/scoring-schema.json` | `recruitment-process-audit` | all `business-operations` scoring skills | The shared, machine-readable contract. Sibling skills set their own `skill` slug and dimension names but reuse every required field and gate. |
| `tools/knowledge_updater.py` | `recruitment-process-audit` | cluster-shared knowledge pipeline | Sibling skills can subclass `Entry`/`Config` and override `SOURCES`, `SEARCH_QUERIES`, `ARXIV_CATEGORIES`, and the `BRAIN` path; the fetch/parse/score/dedup/append pipeline is reused as-is. |

## Imports (what this skill reuses from the cluster)
- This skill is the **origin** of `sub-stakeholder-mapper` and `sub-scoring-engine`, so it currently
  imports no cluster sub-skill. When a sibling skill later publishes a `sub-evidence-collector` or
  `sub-roadmap-prioritizer`, this harness will import it via the same frontmatter contract.

## Exports (what sibling skills reuse from this skill)
- `skills/sub-stakeholder-mapper.md` - reusable as-is (domain-neutral inputs/outputs).
- `skills/sub-scoring-engine.md` - reusable with a skill-specific dimension set.
- `skills/scoring-schema.json` - the canonical output contract (schema_version `1.0.0`).
- `tools/knowledge_updater.py` - reusable knowledge pipeline (subclass-friendly `Config` + `Entry`).

## Standardized scoring output schema (the cross-skill contract)
Sibling skills emit a payload conforming to `skills/scoring-schema.json`. The contract guarantees:
- `schema_version` is present; reusing sub-skills reject unknown major versions.
- All eight canonical dimensions are scored with evidence and a named framework (additional dimensions
  permitted for sibling skills).
- `gates` carries the five non-skippable quality gates.
- Roadmap items each carry effort, impact, and a measurable `success_metric`.
- `degraded_mode == true` forces `confidence == "low"`.

This makes scores comparable across skills and lets benchmark/improvement loops (Scenario 3) run
against any business-operations skill that adopts the schema.

## Wiring contract for reuse
To reuse this skill's sub-skills from a sibling:
1. Reference the sub-skill by relative path: `../recruitment-process-audit/skills/sub-stakeholder-mapper.md`.
2. Invoke it as the documented harness step; respect its Quality Gate (non-skippable).
3. Feed its outputs (stakeholder matrix / scored dimensions) into the sibling harness unchanged.
4. Emit the final deliverable as a `scoring-schema.json`-conformant payload.

To reuse the knowledge pipeline, import `knowledge_updater` and override the domain constants on a
`Config` instance (see `tools/README.md`).

## Success criteria (Phase 5)
- [x] A shared sub-skill is reused from this skill for sibling cluster skills (`sub-stakeholder-mapper`, `sub-scoring-engine`).
- [x] A standardized scoring output schema is published and validated (`skills/scoring-schema.json`, checked by `tests/run_tests.py`).
- [x] Reuse references are documented (this map) and wired by relative path + the schema contract.