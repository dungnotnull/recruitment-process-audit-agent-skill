# CLAUDE.md — Internal Recruitment Process Audit (fairness, bias removal)

**Skill name:** `recruitment-process-audit`
**Tagline:** Audit a hiring process for fairness, effectiveness, and bias removal.
**Source idea:** #103 (cluster: `business-operations`)
**Current phase:** Phase 5 - Integration & Cross-Skill Wiring COMPLETE (all phases 0-5 done)

## Problem This Skill Solves
Recruitment processes leak bias and inconsistency, hurting fairness and hire quality. Teams need an evidence-based audit of structure, validity, and adverse-impact risk.

## Harness Flow Summary
1. **sub-stakeholder-mapper** → Ensure the deliverable accounts for every party who must approve, execute, or be affected by it.
2. **sub-requirements-gatherer** → Capture objectives, stakeholders, constraints, and the document/artifact under review so analysis is complete.
3. **sub-bias-screener** → Surface where bias can enter (sourcing, screening, interview, decision) and flag adverse-impact exposure.
4. **sub-scoring-engine** → Produce a transparent, dimension-by-dimension score (0-100 or band) with evidence for every sub-score.
5. **main (synthesis)** → assemble the scored deliverable + prioritized roadmap and run final quality gates.

## Gates
No safety/compliance gate applies to this cluster; standard quality gates still apply.

## Sub-skills
- `skills/sub-stakeholder-mapper.md` — Map stakeholders, their interests, influence, and success metrics.
- `skills/sub-requirements-gatherer.md` — Elicit and structure the full set of hiring process requirements and context.
- `skills/sub-bias-screener.md` — Screen each stage for bias vectors and adverse-impact risk.
- `skills/sub-scoring-engine.md` — Multi-dimensional scoring of the recruitment process against the selected framework.

## Tools Required
WebSearch, WebFetch, Read, Write, Bash

## Knowledge Sources
- [SIOP (Society for I/O Psychology)](https://www.siop.org)
- [US EEOC Uniform Guidelines](https://www.eeoc.gov)
- [Harvard Business Review hiring research](https://hbr.org)
- [SHRM](https://www.shrm.org)

ArXiv / research categories crawled: cs.CY

## Supporting Tools
- `tools/knowledge_updater.py` — crawl4ai pipeline that refreshes `SECOND-KNOWLEDGE-BRAIN.md` weekly from the sources above.

## Active Development Tasks
- [x] Scaffold deliverables and sub-skills
- [x] Define scoring dimensions against named frameworks
- [x] Expand `SECOND-KNOWLEDGE-BRAIN.md` with first crawl batch (curated, cited seed entries + dedup)
- [x] Add adversarial/edge test scenarios (12 total; deterministic checks in tests/run_tests.py)
- [x] Wire shared cluster sub-skills for reuse (skills/reuse-map.md + skills/scoring-schema.json)

## Reference Docs
- `PROJECT-detail.md` — full technical spec
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` — phase roadmap
- `SECOND-KNOWLEDGE-BRAIN.md` — living domain knowledge base
