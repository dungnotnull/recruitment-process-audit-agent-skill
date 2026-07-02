# Recruitment Process Audit Agent Skill

> Audit a hiring process for fairness, effectiveness, and bias removal - an evidence-based,
> framework-grounded agent skill with a self-improving knowledge base.

[![Status](https://img.shields.io/badge/status-all%20phases%20complete-brightgreen)](PROJECT-DEVELOPMENT-PHASE-TRACKING.md)
[![Tests](https://img.shields.io/badge/tests-24%2F24%20pass-success)](tests/pass-fail-log.md)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](#license)

`recruitment-process-audit` turns an AI agent into an I/O psychologist and talent-acquisition
leader specializing in fair, validated selection. It runs a research-first harness that intakes
the user's case, binds it to named world-renowned frameworks, scores it on 8 dimensions, and
returns a prioritized improvement roadmap with effort/impact and measurable success metrics. The
skill is self-improving: `tools/knowledge_updater.py` continuously refreshes its knowledge base
from authoritative sources.

---

## Table of contents
- [Why this skill exists](#why-this-skill-exists)
- [Key features](#key-features)
- [How it works](#how-it-works)
- [Scoring dimensions](#scoring-dimensions)
- [Evaluation frameworks](#evaluation-frameworks)
- [Quick start](#quick-start)
- [Project structure](#project-structure)
- [The scored deliverable (output schema)](#the-scored-deliverable-output-schema)
- [Self-improving knowledge base](#self-improving-knowledge-base)
- [Cross-skill reuse](#cross-skill-reuse)
- [Testing & validation](#testing--validation)
- [Requirements](#requirements)
- [Configuration](#configuration)
- [Weekly scheduling](#weekly-scheduling)
- [Status & roadmap](#status--roadmap)
- [Contributing](#contributing)
- [Acknowledgments & sources](#acknowledgments--sources)
- [License](#license)

---

## Why this skill exists

Recruitment processes leak bias and inconsistency, hurting both fairness and hire quality. Teams
need an evidence-based audit of structure, validity, and adverse-impact risk - not gut feel.

This skill solves that by:

1. **Binding every judgment to a named, citable framework** - never ad-hoc scoring.
2. **Scoring 8 dimensions transparently**, each with a numeric score and one-line evidence.
3. **Flagging bias and adverse-impact exposure** at every stage (sourcing, screening, interview, decision).
4. **Delivering a prioritized, measurable roadmap** (quick wins / major projects / long-term).
5. **Self-improving**: a weekly pipeline refreshes the knowledge base from authoritative sources.

### Target users
- Talent-acquisition leaders and recruiters who want an expert-grade fairness audit.
- People-ops and DEI teams tracking adverse-impact exposure.
- Hiring managers and legal/compliance partners validating selection procedures.

### Trigger examples
- "Full assessment" - score every dimension with evidence, deliver a prioritized roadmap.
- "Targeted concern" - diagnose a specific screening-validity weakness and return focused, measurable fixes.
- "Benchmark / improvement loop" - re-score against the same rubric, show before/after deltas, update the roadmap.

---

## Key features

- **Research-first harness** with four sub-skills invoked in a fixed, non-skippable order.
- **8-dimension scoring** grounded in 5 world-renowned, citable frameworks.
- **Standardized, machine-readable output schema** (`skills/scoring-schema.json`) so scores are
  comparable across skills and benchmark/improvement loops are portable.
- **Non-skippable quality gates** - every dimension scored with evidence, at least one framework
  cited, roadmap items measurable, and a devil's-advocate pass before output.
- **Self-improving knowledge base** (`SECOND-KNOWLEDGE-BRAIN.md`) refreshed weekly by a
  production-grade crawler with crawl4ai + HTTP/ArXiv-API fallback and URL/DOI dedup.
- **Graceful degradation** - if live sources are unavailable, the skill falls back to the
  knowledge base, lowers confidence, and states the limitation (never silently fabricates).
- **Deterministic test harness** validating structure, gates, schema, and adversarial cases
  without invoking a model.

---

## How it works

```
intake / requirements
   |
   v
sub-stakeholder-mapper  ->  sub-requirements-gatherer  ->  sub-bias-screener  ->  sub-scoring-engine
   |                                                                                       |
   |  named frameworks + multi-dimensional scoring + prioritized roadmap + quality gates   |
   v                                                                                       v
                                              FINAL DELIVERABLE (schema-conformant)
```

**Harness flow** (`skills/main.md`):

1. **sub-stakeholder-mapper** - ensure the deliverable accounts for every party who must approve,
   execute, or be affected by it.
2. **sub-requirements-gatherer** - capture objectives, stakeholders, constraints, and the
   artifact under review so analysis is complete.
3. **sub-bias-screener** - surface where bias can enter and flag adverse-impact exposure.
4. **sub-scoring-engine** - produce a transparent, dimension-by-dimension score with evidence.
5. **Synthesis** - assemble the scored report + prioritized roadmap + executive summary.
6. **Final quality gate** - verify every dimension has evidence, a framework is cited, every
   roadmap item is measurable, and a devil's-advocate pass was run. Only then present output.

---

## Scoring dimensions

| # | Dimension | What it measures |
|---|-----------|------------------|
| 1 | Job-analysis grounding | Is selection tied to a documented, validated job analysis? |
| 2 | Sourcing reach & diversity | Does sourcing reach a broad, diverse applicant pool? |
| 3 | Screening validity | Are screeners job-relevant predictors with validity evidence? |
| 4 | Interview structure | Are interviews structured, behaviorally-anchored, and standardized? |
| 5 | Bias-mitigation controls | Are blind/anonymized screening and calibration in place? |
| 6 | Adverse-impact monitoring | Is the four-fifths rule tracked across protected groups? |
| 7 | Candidate experience | Is candidate experience (NPS-style) measured and acted on? |
| 8 | Decision consistency | Is inter-rater reliability measured and debrief structured? |

Each dimension receives a 0-100 score plus a one-line evidence/justification bound to a named
framework. The weighted total maps to a band: **0-39 critical**, **40-59 developing**,
**60-79 established**, **80-100 leading**.

---

## Evaluation frameworks

Every score is bound to one of these named, citable frameworks:

- **Structured interview validity (Schmidt & Hunter meta-analysis)** - predictor validity ranking.
- **Adverse-impact / four-fifths rule** (Uniform Guidelines, 29 CFR 1607) - disparate-impact screening.
- **Competency-based selection frameworks** - job-relevant criteria.
- **Blind/anonymized screening practices** - bias mitigation.
- **Candidate-experience (NPS) measurement** - process quality.

Evidence hierarchy enforced: Systematic Review > Meta-Analysis > RCT/Benchmark > Cohort/Case
Study > Expert Opinion > Blog.

---

## Quick start

This is an **agent skill** (markdown skill files + a Python knowledge tool), not a standalone app.
Point your agent runtime at `skills/main.md` as the harness entry point.

### 1. Run the skill
Invoke `/recruitment-process-audit` (or load `skills/main.md`) with an artifact to audit. The
harness runs the four sub-skills in order, scores all 8 dimensions with evidence, and returns a
schema-conformant scored deliverable + prioritized roadmap.

### 2. Seed the knowledge base (once, after clone)
```bash
python tools/knowledge_updater.py seed
```
Appends the curated, cited baseline entries (idempotent - deduped by URL/DOI hash).

### 3. Verify everything
```bash
python tests/run_tests.py            # 24/24 deterministic checks, writes tests/pass-fail-log.md
python tools/knowledge_updater.py verify   # validate SECOND-KNOWLEDGE-BRAIN.md format
python tools/knowledge_updater.py status   # JSON status of the knowledge base
```

### 4. (Optional) Run a live crawl
```bash
python tools/knowledge_updater.py run
```
Fetches ArXiv (cs.CY) + the configured authoritative sources, scores, dedupes, and appends new
dated, cited entries.

---

## Project structure

```
recruitment-process-audit-agent-skill/
+- CLAUDE.md                              # Skill overview, harness flow, gates, sources
+- PROJECT-detail.md                      # Full technical spec
+- PROJECT-DEVELOPMENT-PHASE-TRACKING.md  # Phase roadmap (all phases complete)
+- SECOND-KNOWLEDGE-BRAIN.md              # Living, self-improving knowledge base
+- README.md                              # This file
+- .gitignore
+- skills/
|   +- main.md                            # Harness entry point + quality gates
|   +- sub-stakeholder-mapper.md          # Stakeholder (interest x influence) mapping
|   +- sub-requirements-gatherer.md       # Requirements & context elicitation
|   +- sub-bias-screener.md               # Per-stage bias & adverse-impact screening
|   +- sub-scoring-engine.md              # Multi-dimensional evidence-based scoring
|   +- scoring-schema.json                # Standardized scoring output schema (v1.0.0)
|   +- reuse-map.md                       # Cross-skill wiring / shared sub-skill references
+- tools/
|   +- knowledge_updater.py               # Self-improving crawler (crawl4ai + HTTP/ArXiv fallback)
|   +- README.md                          # Tool usage, scheduling, append format
+- tests/
|   +- run_tests.py                       # Dependency-free deterministic test harness
|   +- test-scenarios.md                  # 12 scenarios incl. adversarial/edge
|   +- pass-fail-log.md                   # Recorded results (24/24 PASS)
|   +- fixtures/
|       +- sample-scoring-output.json     # Valid example scoring payload
```

---

## The scored deliverable (output schema)

The final deliverable is a payload conforming to
[`skills/scoring-schema.json`](skills/scoring-schema.json) (`schema_version` `1.0.0`). The schema
enforces the skill's quality gates as a machine-readable contract:

- All 8 canonical dimensions scored, each with `score` (0-100), `evidence`, and `framework`.
- `weighted_total` + `band` (critical / developing / established / leading).
- Ranked `weaknesses` tied to dimensions and evidence.
- `roadmap` items each with `tier`, `effort`, `impact`, a measurable `success_metric`, and `owner`.
- `stakeholders` (interest x influence matrix) and `bias_findings` (per-stage, with mitigations).
- `devils_advocate` pass + five non-skippable `gates`.
- `degraded_mode == true` forces `confidence == "low"`.

See [`tests/fixtures/sample-scoring-output.json`](tests/fixtures/sample-scoring-output.json) for a
complete valid example.

---

## Self-improving knowledge base

[`SECOND-KNOWLEDGE-BRAIN.md`](SECOND-KNOWLEDGE-BRAIN.md) is the living knowledge base. It is grown
weekly by [`tools/knowledge_updater.py`](tools/knowledge_updater.py):

```
fetch (crawl4ai | ArXiv API + HTTP) -> parse -> score (recency x relevance)
    -> dedupe (URL/DOI SHA-256 hash) -> append (dated, cited entries) -> update log
```

- **Sources:** SIOP, US EEOC Uniform Guidelines, Harvard Business Review, SHRM, ArXiv `cs.CY`.
- **Dedup:** entries are keyed by a stable 16-char SHA-256 hash of their DOI/URL, so re-runs never
  duplicate.
- **Append format:** every entry carries a date, authors, year, venue, link, DOI, relevance score,
  key findings, a full citation, and a dedup hash.
- **Graceful degradation:** if `crawl4ai`/`requests` are missing or the network fails, the run
  appends nothing and logs the limitation - the existing knowledge base is never corrupted.

See [`tools/README.md`](tools/README.md) for full CLI reference.

---

## Cross-skill reuse

This skill lives in the `business-operations` cluster. Two capabilities are shared with sibling
skills via [`skills/reuse-map.md`](skills/reuse-map.md):

- **`sub-stakeholder-mapper`** - domain-neutral stakeholder mapping, reused verbatim as a first
  harness step by any business-operations skill.
- **`sub-scoring-engine` + `skills/scoring-schema.json`** - generic multi-dimensional scoring with
  a portable output contract, reused with a skill-specific dimension set.

This makes scores comparable across skills and lets benchmark/improvement loops run against any
business-operations skill that adopts the schema.

---

## Testing & validation

[`tests/run_tests.py`](tests/run_tests.py) is a dependency-free, deterministic harness that
validates the skill's structure and contracts **without invoking a model** (resource-saving,
production-readiness verification). It checks:

- Skill files exist with frontmatter and required sections; sub-skills declare Inputs/Outputs/Gate.
- `main.md` invokes sub-skills in the documented order; all quality gates present.
- `scoring-schema.json` is valid and self-consistent; a valid payload passes and an adversarial
  payload is rejected with >= 4 violations.
- `SECOND-KNOWLEDGE-BRAIN.md` has the documented sections, seed frameworks, dedup hashes, dated
  cited entries, and an update log.
- `knowledge_updater.py` imports cleanly, exposes the documented CLI, and its pure functions
  (hashing, scoring, dedup) are deterministic and idempotent.
- `reuse-map.md` wires the shared sub-skills and the schema contract.

```bash
python tests/run_tests.py
```

Latest result: **24/24 PASS** - see [`tests/pass-fail-log.md`](tests/pass-fail-log.md).
Test scenarios (12, incl. adversarial/edge) are in
[`tests/test-scenarios.md`](tests/test-scenarios.md).

---

## Requirements

- **Python 3.9+** for `tools/knowledge_updater.py` and `tests/run_tests.py`.
- Optional: `pip install crawl4ai` (preferred crawler) and `pip install requests` (HTTP fallback).
- The tools run with **zero optional dependencies** (stdlib only); on network failure they append
  nothing and degrade gracefully.

---

## Configuration

A JSON config can be persisted at `tools/knowledge_updater.config.json` (gitignored). Recognized
keys mirror the `Config` dataclass: `fetcher` (`auto` | `crawl4ai` | `http`), `sources`,
`arxiv_categories`, `search_queries`, `max_arxiv_results`, `min_relevance`. CLI flags override
config values.

---

## Weekly scheduling

```bash
python tools/knowledge_updater.py schedule
```

Installs a weekly task that runs `... run` at 03:00 local time on the weekday it was installed:

- **Linux / macOS:** appends a `crontab` line (idempotent - will not duplicate).
- **Windows:** creates a `schtasks` task `recruitment-process-audit_weekly` running as `SYSTEM`.

A rotating log is written to `tools/knowledge_updater.log` (gitignored).

---

## Status & roadmap

All development phases are complete (see
[`PROJECT-DEVELOPMENT-PHASE-TRACKING.md`](PROJECT-DEVELOPMENT-PHASE-TRACKING.md)):

- Phase 0 - Research & Skill Architecture: done
- Phase 1 - Core Sub-Skills: done
- Phase 2 - Main Harness + Quality Gates: done
- Phase 3 - SECOND-KNOWLEDGE-BRAIN Pipeline: done
- Phase 4 - Testing & Validation: done
- Phase 5 - Integration & Cross-Skill Wiring: done

Future work is driven by the weekly knowledge crawl and live end-to-end scenario runs in
production.

---

## Contributing

Contributions are welcome. Please:

1. Run `python tests/run_tests.py` and ensure 24/24 PASS before submitting.
2. Run `python tools/knowledge_updater.py verify` after any knowledge-base change.
3. Keep every score bound to a named, citable framework - never ad-hoc.
4. Never add silent assumptions; surface unknowns explicitly.

---

## Acknowledgments & sources

This skill is grounded in authoritative, citable sources:

- Schmidt, F. L., & Hunter, J. E. (1998). *Validity and utility of selection methods in personnel
  psychology.* Psychological Bulletin. https://doi.org/10.1037/0033-2909.124.2.262
- Levashina, J., et al. (2014). *The structured employment interview: Narrative and quantitative
  review.* Personnel Psychology. https://doi.org/10.1111/peps.12109
- Uniform Guidelines on Employee Selection Procedures (29 CFR 1607), U.S. EEOC.
  https://www.eeoc.gov
- Bohnet, I. (2016). *What Works: Gender Equality by Design.* Harvard University Press.
- Barrick, M. R., & Mount, M. K. (1991). *Meta-analysis of personality and cognitive ability to
  job performance.* Personnel Psychology. https://doi.org/10.1111/j.1744-6570.1991.tb00688.x
- Hausknecht, J. P., Day, D. V., & Thomas, S. C. (2004). *Applicant reactions to selection
  procedures.* Personnel Psychology. https://doi.org/10.1111/j.1744-6570.2004.tb00483.x
- SIOP (Society for I/O Psychology) - https://www.siop.org
- SHRM (Society for Human Resource Management) - https://www.shrm.org

---

## License

Released under the **MIT License**. See the repository for terms. You are free to use, modify, and
distribute this skill, including for commercial hiring-process audits, provided the license and
copyright notice are included.