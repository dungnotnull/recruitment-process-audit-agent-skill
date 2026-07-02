# PROJECT-detail.md — Internal Recruitment Process Audit (fairness, bias removal)

## Executive Summary
`recruitment-process-audit` turns Claude into an I/O psychologist and talent-acquisition leader specializing in fair, validated selection. It runs a research-first harness that intakes the user's case, binds it to named world-renowned frameworks, scores it on 8 dimensions, and returns a prioritized improvement roadmap with effort/impact. The skill is self-improving: `tools/knowledge_updater.py` continuously refreshes its knowledge base from authoritative sources.

## Problem Statement
Recruitment processes leak bias and inconsistency, hurting fairness and hire quality. Teams need an evidence-based audit of structure, validity, and adverse-impact risk.

## Target Users & Use Cases
- Primary: practitioners and non-experts who need an expert-grade, evidence-based assessment of their internal recruitment process audit (fairness, bias removal) artifact.
- Trigger examples:
  - User says: "Full assessment" → skill score every dimension with evidence, highlight job-analysis grounding and sourcing reach & diversity findings, deliver a prioritized roadmap
  - User says: "Targeted concern" → skill diagnose the screening validity issue against the named framework and return focused, measurable fixes
  - User says: "Benchmark / improvement loop" → skill re-score against the same rubric, show the before/after delta per dimension, and update the roadmap

## Harness Architecture
```
intake/requirements
    │  stakeholder-mapper → requirements-gatherer → bias-screener → scoring-engine → synthesis
    ▼
[named frameworks] → [multi-dimensional scoring] → [prioritized roadmap] → [quality/compliance gates] → DELIVERABLE
```

## Evaluation Frameworks (world-renowned, citable)
- **Structured interview validity (Schmidt & Hunter meta-analysis)** — Predictor validity ranking
- **Adverse-impact / four-fifths rule** — Disparate-impact screening
- **Competency-based selection frameworks** — Job-relevant criteria
- **Blind/anonymized screening practices** — Bias mitigation
- **Candidate-experience (NPS) measurement** — Process quality

## Scoring Dimensions
1. Job-analysis grounding
2. Sourcing reach & diversity
3. Screening validity
4. Interview structure
5. Bias-mitigation controls
6. Adverse-impact monitoring
7. Candidate experience
8. Decision consistency

## Full Sub-Skill Catalog
### `sub-stakeholder-mapper`
- **Purpose:** Ensure the deliverable accounts for every party who must approve, execute, or be affected by it.
- **Inputs:** Org/project brief
- **Outputs:** Stakeholder matrix (interest x influence) with each party's success metric and likely objections
- **Tools:** Read
- **Quality gate:** All decision-makers and affected groups listed with interest and influence ratings.
### `sub-requirements-gatherer`
- **Purpose:** Capture objectives, stakeholders, constraints, and the document/artifact under review so analysis is complete.
- **Inputs:** User brief, uploaded documents, clarifying answers
- **Outputs:** Structured requirements pack with scope, stakeholders, and explicit out-of-scope items
- **Tools:** Read, WebSearch
- **Quality gate:** Scope, stakeholders, and success criteria all captured; ambiguities flagged for confirmation.
### `sub-bias-screener`
- **Purpose:** Surface where bias can enter (sourcing, screening, interview, decision) and flag adverse-impact exposure.
- **Inputs:** Process map, criteria, any outcome data
- **Outputs:** Bias-risk findings per stage with mitigation
- **Tools:** Read, WebSearch
- **Quality gate:** Each process stage is checked for at least one bias vector with a concrete mitigation.
### `sub-scoring-engine`
- **Purpose:** Produce a transparent, dimension-by-dimension score (0-100 or band) with evidence for every sub-score.
- **Inputs:** Normalized profile, selected framework + rubric
- **Outputs:** Per-dimension scores, weighted total, strengths, and ranked weaknesses each tied to evidence
- **Tools:** Read, WebSearch
- **Quality gate:** Every dimension has a numeric score AND a one-line evidence/justification; no unscored dimension.

## Skill File Format Specification
Each skill file uses YAML frontmatter (`name`, `description`) followed by: Role & Persona, Workflow (Harness Flow), Sub-skills Available, Tools, Output Format, Quality Gates. `skills/main.md` is the harness entry point and invokes the sub-skills above in order.

## E2E Execution Flow
1. Parse the user request and uploaded artifact(s).
2. Run intake/requirements sub-skill; flag unknowns (no silent assumptions).
3. (No safety gate for this cluster.)
4. Select governing framework(s) and rubric.
5. Score every dimension with cited evidence.
6. Generate the prioritized roadmap (effort/impact + success metric).
7. Run quality/devil's-advocate review.
8. Synthesize the final professional deliverable; pass all quality gates before display.

## SECOND-KNOWLEDGE-BRAIN Integration
- Sources: SIOP (Society for I/O Psychology), US EEOC Uniform Guidelines, Harvard Business Review hiring research, SHRM
- ArXiv categories: cs.CY
- Search queries: "structured interview validity hiring", "adverse impact bias selection", "recruitment fairness metrics"
- Append format: dated entries with Title, Authors, Year, Venue, DOI/Link, Relevance.

## Supporting Tools Spec
`tools/knowledge_updater.py`: crawl4ai → fetch → parse → score (recency × relevance) → dedupe (URL/DOI hash) → append to `SECOND-KNOWLEDGE-BRAIN.md`. Schedule: weekly cron.

## Quality Gates (must all pass before output)
- Every scored dimension has evidence.
- At least one named framework cited.
- Roadmap items each have effort, impact, and a measurable success metric.
- Devil's-advocate review passed.

## Test Scenarios
1. **Full assessment** — Input: User submits a complete internal recruitment process audit artifact and asks for a full evaluation → Expected: Score every dimension with evidence, highlight job-analysis grounding and sourcing reach & diversity findings, deliver a prioritized roadmap
2. **Targeted concern** — Input: User reports a specific weakness in screening validity → Expected: Diagnose the screening validity issue against the named framework and return focused, measurable fixes
3. **Benchmark / improvement loop** — Input: User wants to compare a revised version against a prior baseline → Expected: Re-score against the same rubric, show the before/after delta per dimension, and update the roadmap

## Key Design Decisions
1. Scoring is always bound to named, citable frameworks — never ad hoc.
2. Intake forbids silent assumptions; unknowns are surfaced.
3. Roadmap is effort/impact-ranked and measurable.
4. Knowledge base is self-updating for trend alignment.
5. Devil's-advocate review is mandatory before output.
