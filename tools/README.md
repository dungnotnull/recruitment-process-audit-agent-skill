 tools/ - Self-Improving Knowledge Pipeline

`knowledge_updater.py` is the production-grade, self-improving crawler that keeps
`SECOND-KNOWLEDGE-BRAIN.md` aligned with the latest evidence on fair, validated,
bias-free recruitment. It implements the pipeline defined in `PROJECT-detail.md`
and `CLAUDE.md`.

## Pipeline

```
fetch (crawl4ai | ArXiv API + HTTP) -> parse -> score (recency * relevance)
    -> dedupe (URL/DOI SHA-256 hash) -> append (dated, cited entries) -> update log
```

The crawler **prefers** `crawl4ai` when installed and **degrades gracefully** to a
plain HTTP + ArXiv Atom API backend (stdlib `urllib` plus optional `requests`)
when `crawl4ai` is absent or network calls fail. The existing knowledge base is
never corrupted on failure - the run simply appends nothing and logs the
limitation (Design Principle 8: graceful degradation).

## Requirements

- Python 3.9+
- Optional: `crawl4ai` (preferred crawler) - `pip install crawl4ai`
- Optional: `requests` (HTTP fallback) - `pip install requests`
- The tool runs with zero optional dependencies (stdlib only), appending nothing
  on network failure.

## Commands

```bash
# Append curated, cited seed entries (idempotent, deduped) - run once after clone
python tools/knowledge_updater.py seed

# Run a full crawl + append cycle (ArXiv cs.CY + SIOP/EEOC/HBR/SHRM source scans)
python tools/knowledge_updater.py run
python tools/knowledge_updater.py run --sources siop eeoc --fetcher http
python tools/knowledge_updater.py run --dry-run          # preview, no writes
python tools/knowledge_updater.py run --max-arxiv 100

# Install a weekly scheduled task (cron on Linux/macOS, schtasks on Windows)
python tools/knowledge_updater.py schedule

# Print knowledge-base status as JSON
python tools/knowledge_updater.py status

# Validate the brain file conforms to the documented append format
python tools/knowledge_updater.py verify

python tools/knowledge_updater.py --help
```

Exit codes: `0` success, `1` transient runtime error, `2` config/usage error,
`3` scheduling platform unsupported.

## Configuration

A JSON config can be persisted at `tools/knowledge_updater.config.json`
(written by `Config.save()`). Recognized keys mirror the `Config` dataclass:
`fetcher`, `sources`, `arxiv_categories`, `search_queries`, `max_arxiv_results`,
`min_relevance`. CLI flags override config values.

## Weekly Scheduling

The `schedule` command installs a weekly task that runs `... run` at 03:00 local
time on the weekday it was installed:

- **Linux / macOS:** appends a `crontab` line (idempotent - will not duplicate).
  To remove manually: `crontab -l | grep -v recruitment-process-audit | crontab -`.
- **Windows:** creates a `schtasks` task named `recruitment-process-audit_weekly`
  running as `SYSTEM`. To remove manually:
  `schtasks /Delete /TN recruitment-process-audit_weekly /F`.

A rotating log is written to `tools/knowledge_updater.log`.

## Append Format (consumed by the skill)

Each appended entry carries a date, citation, and dedup hash so the skill can
trace every claim to a source and so re-runs never duplicate:

```
### [YYYY-MM-DD] Title
- Authors: ...
- Year: ...
- Venue: ...
- Link: ...
- DOI: ...
- Relevance score: 0.0-1.0
- Key findings: ...
- Citation: ...
<!--hash:<16-hex>-->
```

## Verification

`python tools/knowledge_updater.py verify` checks that every crawl batch carries
dedup hashes and that the Knowledge Update Log section is present - a cheap,
deterministic integrity gate suitable for CI.
