# Test Scenarios - Internal Recruitment Process Audit (fairness, bias removal)

These scenarios validate the harness, scoring, gates, schema, and graceful
degradation. Minimum 8; adversarial and edge cases included. Scenarios 8 and 10
are deterministically validated by `tests/run_tests.py` (no model invocation) and
recorded in `tests/pass-fail-log.md`; the remainder are validated end-to-end by the
model harness in production.

## Scenario 1: Full assessment
- **Input:** User submits a complete internal recruitment process audit artifact and asks for a full evaluation
- **Expected behavior:** Score every dimension with evidence, highlight job-analysis grounding and sourcing reach & diversity findings, deliver a prioritized roadmap
- **Frameworks expected in output:** Structured interview validity (Schmidt & Hunter meta-analysis), Adverse-impact / four-fifths rule
- **Quality gates checked:** every dimension scored with evidence; roadmap items measurable.
- **Pass criteria:** output conforms to `skills/scoring-schema.json`; contains a scorecard, evidence per dimension, and a prioritized roadmap; no silent assumptions.

## Scenario 2: Targeted concern
- **Input:** User reports a specific weakness in screening validity
- **Expected behavior:** Diagnose the screening validity issue against the named framework and return focused, measurable fixes
- **Frameworks expected in output:** Structured interview validity (Schmidt & Hunter meta-analysis), Adverse-impact / four-fifths rule
- **Quality gates checked:** every dimension scored with evidence; roadmap items measurable.
- **Pass criteria:** output contains a focused screening-validity diagnosis, evidence per dimension, and a measurable fix roadmap; no silent assumptions.

## Scenario 3: Benchmark / improvement loop
- **Input:** User wants to compare a revised version against a prior baseline
- **Expected behavior:** Re-score against the same rubric, show the before/after delta per dimension, and update the roadmap
- **Frameworks expected in output:** Structured interview validity (Schmidt & Hunter meta-analysis), Adverse-impact / four-fifths rule
- **Quality gates checked:** every dimension scored with evidence; roadmap items measurable; `artifact.deltas` populated.
- **Pass criteria:** output carries per-dimension `before`/`after`/`delta` and a refreshed roadmap; deltas are consistent with the weighted_total delta.

## Scenario 4: Incomplete input (edge case)
- **Input:** User provides only a vague one-line description with no artifact.
- **Expected behavior:** Intake sub-skill flags missing mandatory fields and asks targeted clarifying questions instead of fabricating a score.
- **Pass criteria:** No score is produced from assumptions; unknowns are explicitly listed; `gates.no_silent_assumptions == true` forces a clarifying turn before scoring.

## Scenario 5: Offline / sources unavailable (graceful degradation)
- **Input:** A normal request, but WebSearch/WebFetch are unavailable.
- **Expected behavior:** Skill falls back to SECOND-KNOWLEDGE-BRAIN.md and clearly states the limitation and reduced confidence.
- **Pass criteria:** Output sets `degraded_mode == true` and `confidence == "low"`; still cites internal frameworks.

## Scenario 6: Adversarial - conflicting stakeholder requirements (edge case)
- **Input:** Two approvers demand mutually exclusive outcomes (e.g. Legal requires four-fifths compliance while a Hiring Manager demands the fastest possible time-to-hire with minimal process).
- **Expected behavior:** `sub-stakeholder-mapper` surfaces the conflict explicitly; `sub-requirements-gatherer` flags the ambiguity; the skill never silently picks one side. Roadmap reflects a compliance-preserving compromise.
- **Pass criteria:** Stakeholder matrix records both approvers with conflicting `likely_objections`; an explicit conflict is surfaced (no silent assumption); roadmap items satisfy both success metrics.

## Scenario 7: Adversarial - fabricated / uncited scoring claim must be rejected
- **Input:** A draft assessment asserts a high "Screening validity" score with no framework binding and no evidence (e.g. "feels valid").
- **Expected behavior:** The scoring-engine quality gate rejects the unscored/uncited dimension; devil's-advocate pass challenges the unsupported claim; output is withheld until revised.
- **Pass criteria:** `gates.every_dimension_scored_with_evidence == true` and `gates.at_least_one_framework_cited == true`; a dimension with empty `evidence` or empty `framework` cannot be emitted.

## Scenario 8: Adversarial - schema-violating output is rejected by the validator (deterministic)
- **Input:** A scoring payload missing the `success_metric` on a roadmap item, `frameworks: []`, `dimensions: []`, `weighted_total: 150`, an invalid `band`, and an extra `rogue_field`.
- **Expected behavior:** `skills/scoring-schema.json` validation (mirrored by `tests/run_tests.py`) rejects the payload with >= 4 distinct violations.
- **Pass criteria:** `tests/run_tests.py` `schema rejects adversarial payload` check PASSES (>= 4 violations reported). Validated in `tests/pass-fail-log.md`.

## Scenario 9: Adversarial - biased language in artifact flagged by bias-screener
- **Input:** An artifact contains culture-fit / "aggressive hunger" / "young and energetic" sourcing language and an unstructured "gut feel" interview stage.
- **Expected behavior:** `sub-bias-screener` flags sourcing homophily + age-coded language and the unstructured interview as bias vectors with concrete mitigations and adverse-impact exposure.
- **Pass criteria:** `bias_findings` includes at least one entry per stage (sourcing, screening, interview, decision); every entry has a non-empty `mitigation`; adverse-impact exposure is flagged.

## Scenario 10: Adversarial - knowledge-updater dedup idempotence (deterministic)
- **Input:** Run `knowledge_updater.py seed` / append twice with identical entries.
- **Expected behavior:** The first run appends entries; the second run appends zero (URL/DOI hash dedup).
- **Pass criteria:** `tests/run_tests.py` `append_entries dedup` check PASSES (first=1, second=0). Validated in `tests/pass-fail-log.md`.

## Scenario 11: Adversarial - re-scorer consistency / no silent drift
- **Input:** Re-score the same unchanged artifact twice with the same rubric.
- **Expected behavior:** Identical dimension scores and weighted_total; any drift must be explained (never silent).
- **Pass criteria:** Re-runs yield identical `weighted_total` and per-dimension scores, or any difference is justified in `devils_advocate.challenged`; `gates.no_silent_assumptions == true`.

## Scenario 12: Adversarial - gate blocking on missing roadmap measurability
- **Input:** A roadmap item with effort and impact but no measurable success metric (e.g. "improve fairness").
- **Expected behavior:** Final quality gate rejects the item; output withheld until every roadmap item carries a measurable success metric.
- **Pass criteria:** `gates.roadmap_items_measurable == true`; a roadmap item with empty `success_metric` cannot be emitted (enforced by `scoring-schema.json` `minLength: 1`).

## Validation mapping
| Scenario | Deterministic (tests/run_tests.py) | Production (model harness) |
|----------|------------------------------------|----------------------------|
| 1, 2, 3  | structure + schema shape           | full end-to-end run         |
| 4        | `no_silent_assumptions` gate       | clarifying-turn behavior    |
| 5        | `degraded_mode` + `confidence`    | offline fallback run        |
| 6        | stakeholder conflict surfacing     | full end-to-end run         |
| 7        | gate enforcement (evidence/framework) | full end-to-end run       |
| 8        | YES - `schema rejects adversarial payload` | -                  |
| 9        | bias_findings per-stage coverage   | full end-to-end run         |
| 10       | YES - `append_entries dedup`        | -                          |
| 11       | `relevance_score` determinism      | full end-to-end run         |
| 12       | roadmap `success_metric` minLength | full end-to-end run         |