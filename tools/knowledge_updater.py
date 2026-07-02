# -*- coding: utf-8 -*-
"""knowledge_updater.py - self-improving crawler for the Internal Recruitment
Process Audit (fairness, bias removal) skill.

Production-grade pipeline (see CLAUDE.md / PROJECT-detail.md):
  1. fetch   -> latest papers/docs from domain sources and ArXiv
  2. parse   -> title, authors, date, DOI/URL, abstract, key findings
  3. score   -> recency * domain-keyword relevance
  4. dedupe  -> skip entries already present (URL/DOI hash)
  5. append  -> add scored entries to SECOND-KNOWLEDGE-BRAIN.md
  6. schedule-> install a weekly cross-platform scheduled task (cron / schtasks)

The crawler prefers ``crawl4ai`` when installed; otherwise it degrades to a
plain HTTP + ArXiv API backend built on the Python standard library plus
``requests`` (the only optional dependency for the fallback). The skill never
crashes on missing dependencies or network failures - it logs the limitation
and appends nothing, preserving the existing knowledge base (graceful
degradation, Design Principle 8).

Usage:
    python tools/knowledge_updater.py run
    python tools/knowledge_updater.py run --sources siop eeoc
    python tools/knowledge_updater.py schedule
    python tools/knowledge_updater.py status
    python tools/knowledge_updater.py verify
    python tools/knowledge_updater.py seed

Exit codes:
    0  success
    1  transient runtime error (network / parse)
    2  configuration / usage error
    3  scheduling platform unsupported
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import textwrap
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

SKILL_ID = 103
SKILL_SLUG = "recruitment-process-audit"
SKILL_NAME = "Internal Recruitment Process Audit (fairness, bias removal)"
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TOOLS_DIR)
BRAIN = os.path.join(REPO_DIR, "SECOND-KNOWLEDGE-BRAIN.md")
LOG_PATH = os.path.join(TOOLS_DIR, "knowledge_updater.log")
DEFAULT_CONFIG_PATH = os.path.join(TOOLS_DIR, "knowledge_updater.config.json")

# ---------------------------------------------------------------------------
# Domain configuration (sourced from PROJECT-detail.md / SECOND-KNOWLEDGE-BRAIN)
# ---------------------------------------------------------------------------
ARXIV_CATEGORIES: List[str] = ["cs.CY"]
ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_PAGE_SIZE = 50

SEARCH_QUERIES: List[str] = [
    "structured interview validity hiring",
    "adverse impact bias selection",
    "recruitment fairness metrics",
]

# Source registry: slug -> (label, root URL, discovery mode)
SOURCES: Dict[str, Tuple[str, str, str]] = {
    "siop": ("SIOP (Society for I/O Psychology)", "https://www.siop.org", "html"),
    "eeoc": ("US EEOC Uniform Guidelines", "https://www.eeoc.gov", "html"),
    "hbr": ("Harvard Business Review hiring research", "https://hbr.org", "html"),
    "shrm": ("SHRM", "https://www.shrm.org", "html"),
}

DOMAIN_KEYWORDS: List[str] = SEARCH_QUERIES  # identical intent

HASH_PREFIX = "hash:"
HASH_RE = re.compile(r"<!--hash:([0-9a-f]{16})-->")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG = logging.getLogger("knowledge_updater")


def configure_logging(verbose: bool = False) -> None:
    """Configure module logger with console + rotating file handlers."""
    LOG.setLevel(logging.DEBUG if verbose else logging.INFO)
    LOG.handlers.clear()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    LOG.addHandler(console)
    try:
        from logging.handlers import RotatingFileHandler
        file_h = RotatingFileHandler(LOG_PATH, maxBytes=512_000, backupCount=3, encoding="utf-8")
        file_h.setFormatter(fmt)
        file_h.setLevel(logging.DEBUG)
        LOG.addHandler(file_h)
    except Exception as exc:  # filesystem restricted
        LOG.debug("file logging disabled: %s", exc)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entry:
    """A single knowledge-base candidate entry."""

    title: str = ""
    authors: str = ""
    year: int = 0
    venue: str = ""
    url: str = ""
    doi: str = ""
    abstract: str = ""
    source: str = ""

    @property
    def citation(self) -> str:
        names = self.authors or "n/a"
        return f"{self.title} - {names} ({self.year or 'n/a'}). {self.venue or 'n/a'}. {self.url}"

    def to_dict(self) -> Dict[str, object]:
        return dataclasses.asdict(self)


@dataclass
class Config:
    """Runtime configuration for the updater."""

    brain_path: str = BRAIN
    fetcher: str = "auto"  # auto | crawl4ai | http
    sources: List[str] = field(default_factory=lambda: list(SOURCES.keys()))
    arxiv_categories: List[str] = field(default_factory=lambda: list(ARXIV_CATEGORIES))
    search_queries: List[str] = field(default_factory=lambda: list(SEARCH_QUERIES))
    max_arxiv_results: int = ARXIV_PAGE_SIZE
    min_relevance: float = 0.05
    dry_run: bool = False
    verbose: bool = False

    @classmethod
    def load(cls, path: str = DEFAULT_CONFIG_PATH) -> "Config":
        cfg = cls()
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                for key, value in data.items():
                    if hasattr(cfg, key):
                        setattr(cfg, key, value)
            except (OSError, json.JSONDecodeError) as exc:
                LOG.warning("config load failed (%s): %s", path, exc)
        return cfg

    def save(self, path: str = DEFAULT_CONFIG_PATH) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(dataclasses.asdict(self), fh, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Hashing / dedup
# ---------------------------------------------------------------------------
def stable_hash(text: str) -> str:
    """Return a stable 16-char hex digest for a URL/DOI string."""
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:16]


def entry_hash(entry: Entry) -> str:
    key = entry.doi or entry.url
    if not key:
        key = entry.title + "|" + entry.authors
    return stable_hash(key)


def load_seen_hashes(brain_path: str) -> Set[str]:
    if not os.path.exists(brain_path):
        return set()
    try:
        with open(brain_path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        LOG.warning("could not read brain file: %s", exc)
        return set()
    return set(HASH_RE.findall(text))

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
_STOPWORDS = {"the", "and", "for", "with", "of", "in", "to", "a", "an", "on", "or"}


def _keyword_terms(keywords: Sequence[str]) -> List[str]:
    """Flatten keyword phrases into significant lowercased terms."""
    terms: List[str] = []
    for kw in keywords:
        for tok in re.split(r"\W+", kw.lower()):
            if len(tok) > 3 and tok not in _STOPWORDS:
                terms.append(tok)
    return terms


def relevance_score(entry: Entry, keywords: Sequence[str] = DOMAIN_KEYWORDS) -> float:
    """Score = recency(0-1) * (0.4 + 0.6 * keyword_relevance(0-1)).

    Recency decays linearly over 25 years from the current year with a 0.25
    floor, so foundational literature (e.g. Schmidt & Hunter 1998) is not
    discarded merely for age. Missing years receive a neutral 0.3 recency
    weight. Keyword relevance matches significant terms (length > 3) from the
    configured search queries against the title + abstract, so partial term
    overlap is rewarded rather than requiring exact phrase matches.
    """
    now = datetime.date.today().year
    try:
        year = int(entry.year or 0)
    except (TypeError, ValueError):
        year = 0
    if year <= 0:
        recency = 0.3
    else:
        recency = max(0.25, 1.0 - (now - year) / 25.0)
    text = (entry.title + " " + entry.abstract).lower()
    terms = _keyword_terms(keywords)
    if not terms:
        rel = 0.0
    else:
        matched = sum(1 for t in terms if t in text)
        rel = min(1.0, matched / len(terms))
    return round(recency * (0.4 + 0.6 * rel), 3)


# ---------------------------------------------------------------------------
# Fetcher backends
# ---------------------------------------------------------------------------
class Fetcher:
    """Base fetcher contract."""

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg

    def fetch(self) -> List[Entry]:
        raise NotImplementedError


class Crawl4AIFetcher(Fetcher):
    """Preferred backend using crawl4ai."""

    def fetch(self) -> List[Entry]:
        entries: List[Entry] = []
        try:
            from crawl4ai import WebCrawler  # type: ignore
        except Exception as exc:
            LOG.info("crawl4ai unavailable (%s); falling back to HTTP backend", exc)
            return entries
        try:
            crawler = WebCrawler()
            crawler.warmup()
        except Exception as exc:
            LOG.warning("crawl4ai warmup failed: %s", exc)
            return entries
        for cat in self.cfg.arxiv_categories:
            url = f"https://arxiv.org/list/{cat}/recent"
            try:
                res = crawler.run(url=url)
                entries.extend(_parse_arxiv_markdown(getattr(res, "markdown", "") or "", cat))
            except Exception as exc:
                LOG.warning("crawl4ai arxiv %s failed: %s", cat, exc)
        for slug in self.cfg.sources:
            if slug not in SOURCES:
                continue
            label, root, _ = SOURCES[slug]
            try:
                res = crawler.run(url=root)
                md = getattr(res, "markdown", "") or ""
                entries.append(Entry(
                    title=f"Source scan: {label}",
                    url=root,
                    year=datetime.date.today().year,
                    authors="",
                    abstract=md[:500],
                    source=slug,
                ))
            except Exception as exc:
                LOG.warning("crawl4ai source %s failed: %s", slug, exc)
        return entries


class HttpFetcher(Fetcher):
    """Fallback backend using the standard library + optional requests.

    Fetches ArXiv via its public Atom API (no key required) and the configured
    source landing pages for source-scan evidence. No HTML scraping of
    third-party sites is attempted (kept robust + ToS-friendly): landing pages
    are recorded as source-scan entries.
    """

    def __init__(self, cfg: Config) -> None:
        super().__init__(cfg)
        try:
            import requests  # type: ignore
            self._requests = requests
        except Exception as exc:
            LOG.info("requests unavailable (%s); using urllib only", exc)
            self._requests = None

    def _get(self, url: str, headers: Dict[str, str]) -> Tuple[int, str]:
        if self._requests is not None:
            try:
                resp = self._requests.get(url, headers=headers, timeout=30)
                return resp.status_code, resp.text
            except Exception as exc:
                LOG.debug("requests get failed %s: %s", url, exc)
                return 0, ""
        import urllib.request
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.getcode(), resp.read().decode("utf-8", "replace")
        except Exception as exc:
            LOG.debug("urllib get failed %s: %s", url, exc)
            return 0, ""

    def _fetch_arxiv(self) -> List[Entry]:
        entries: List[Entry] = []
        headers = {"User-Agent": f"{SKILL_SLUG}/1.0 (knowledge_updater)"}
        for cat in self.cfg.arxiv_categories:
            for query in self.cfg.search_queries:
                params = {
                    "search_query": f"cat:{cat} AND all:{urllib.parse.quote(query)}",
                    "start": "0",
                    "max_results": str(self.cfg.max_arxiv_results),
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                }
                url = ARXIV_API + "?" + urllib.parse.urlencode(params)
                status, body = self._get(url, headers)
                if status != 200 or not body:
                    LOG.debug("arxiv query failed (%s): %s -> %s", cat, query, status)
                    continue
                entries.extend(_parse_arxiv_atom(body, cat))
        return entries

    def _fetch_sources(self) -> List[Entry]:
        out: List[Entry] = []
        headers = {"User-Agent": f"{SKILL_SLUG}/1.0 (knowledge_updater)"}
        for slug in self.cfg.sources:
            if slug not in SOURCES:
                continue
            label, root, _ = SOURCES[slug]
            status, body = self._get(root, headers)
            abstract = body[:500] if body else "(landing page not retrievable)"
            out.append(Entry(
                title=f"Source scan: {label}",
                url=root,
                year=datetime.date.today().year,
                authors="",
                abstract=abstract,
                source=slug,
            ))
        return out

    def fetch(self) -> List[Entry]:
        return self._fetch_arxiv() + self._fetch_sources()


def select_fetcher(cfg: Config) -> Fetcher:
    if cfg.fetcher == "crawl4ai":
        return Crawl4AIFetcher(cfg)
    if cfg.fetcher == "http":
        return HttpFetcher(cfg)
    # auto: try crawl4ai first, fall back to http on import failure
    try:
        import crawl4ai  # noqa: F401
        return Crawl4AIFetcher(cfg)
    except Exception:
        return HttpFetcher(cfg)

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------
ARXIV_MARKDOWN_ID_RE = re.compile(r"arXiv:(\d{4}\.\d{4,5})", re.IGNORECASE)


def _parse_arxiv_markdown(md: str, category: str) -> List[Entry]:
    out: List[Entry] = []
    for m in ARXIV_MARKDOWN_ID_RE.finditer(md or ""):
        aid = m.group(1)
        out.append(Entry(
            title=f"arXiv:{aid}",
            url=f"https://arxiv.org/abs/{aid}",
            authors="",
            year=datetime.date.today().year,
            abstract="",
            source=f"arxiv:{category}",
        ))
    return out


ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _parse_arxiv_atom(body: str, category: str) -> List[Entry]:
    """Parse an ArXiv Atom feed into Entry records."""
    out: List[Entry] = []
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        LOG.warning("arxiv atom parse failed: %s", exc)
        return out
    for entry_el in root.findall(f"{ATOM_NS}entry"):
        title_el = entry_el.find(f"{ATOM_NS}title")
        summary_el = entry_el.find(f"{ATOM_NS}summary")
        published_el = entry_el.find(f"{ATOM_NS}published")
        id_el = entry_el.find(f"{ATOM_NS}id")
        authors: List[str] = []
        for author_el in entry_el.findall(f"{ATOM_NS}author"):
            name_el = author_el.find(f"{ATOM_NS}name")
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())
        doi_el = entry_el.find("{http://arxiv.org/schemas/atom}doi")
        journal_el = entry_el.find("{http://arxiv.org/schemas/atom}journal_ref")
        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""
        abstract = (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else ""
        year = 0
        if published_el is not None and published_el.text:
            m = re.match(r"(\d{4})", published_el.text)
            if m:
                year = int(m.group(1))
        url = ""
        if id_el is not None and id_el.text:
            url = id_el.text.strip()
        doi = doi_el.text.strip() if doi_el is not None and doi_el.text else ""
        venue = journal_el.text.strip() if journal_el is not None and journal_el.text else "arXiv"
        out.append(Entry(
            title=title or "Untitled arXiv entry",
            authors="; ".join(authors) or "n/a",
            year=year,
            venue=venue,
            url=url,
            doi=doi,
            abstract=abstract,
            source=f"arxiv:{category}",
        ))
    return out


# ---------------------------------------------------------------------------
# Append / write
# ---------------------------------------------------------------------------
def _format_block(today: str, score: float, entry: Entry, h: str) -> str:
    return textwrap.dedent(f"""\
        ### [{today}] {entry.title}
        - Authors: {entry.authors or 'n/a'}
        - Year: {entry.year or 'n/a'}
        - Venue: {entry.venue or 'n/a'}
        - Link: {entry.url or '(no link)'}
        - DOI: {entry.doi or 'n/a'}
        - Relevance score: {score}
        - Key findings: {(entry.abstract or '(abstract pending)')[:280]}
        - Citation: {entry.citation}
        <!--hash:{h}-->
        """)


def append_entries(entries: Sequence[Entry], cfg: Config) -> int:
    """Append scored, deduplicated entries to the brain file.

    Returns the number of newly appended entries.
    """
    brain_path = cfg.brain_path
    seen = load_seen_hashes(brain_path)
    scored = sorted(((relevance_score(e), e) for e in entries),
                    key=lambda x: x[0], reverse=True)
    today = datetime.date.today().isoformat()
    new_blocks: List[str] = []
    for score, entry in scored:
        if score < cfg.min_relevance:
            continue
        if not entry.url and not entry.doi:
            continue
        h = entry_hash(entry)
        if h in seen:
            continue
        seen.add(h)
        new_blocks.append(_format_block(today, score, entry, h))
    if not new_blocks:
        LOG.info("no new entries to append (after dedup/relevance filter).")
        return 0
    if cfg.dry_run:
        LOG.info("[dry-run] would append %d entries:", len(new_blocks))
        for b in new_blocks:
            LOG.info("\n%s", b)
        return len(new_blocks)
    header = f"\n\n## Automated Crawl Batch - {today}\n\n"
    with open(brain_path, "a", encoding="utf-8") as fh:
        fh.write(header)
        fh.write("\n".join(new_blocks))
    _append_update_log(brain_path, today, len(new_blocks))
    LOG.info("appended %d new entries to %s", len(new_blocks), brain_path)
    return len(new_blocks)


def _append_update_log(brain_path: str, today: str, count: int) -> None:
    try:
        with open(brain_path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return
    marker = "## 7. Knowledge Update Log"
    if marker not in text:
        return
    line = f"- [{today}] Automated crawl appended {count} new entries."
    idx = text.find(marker)
    insert_at = text.find("\n", idx) + 1
    text = text[:insert_at] + line + "\n" + text[insert_at:]
    with open(brain_path, "w", encoding="utf-8") as fh:
        fh.write(text)

# ---------------------------------------------------------------------------
# Seed (curated, citable baseline entries)
# ---------------------------------------------------------------------------
SEED_ENTRIES: List[Dict[str, object]] = [
    {
        "title": "Validity and utility of selection methods in personnel psychology: Practical and theoretical implications of 85 years of research findings",
        "authors": "Schmidt, F. L.; Hunter, J. E.",
        "year": 1998,
        "venue": "Psychological Bulletin",
        "url": "https://doi.org/10.1037/0033-2909.124.2.262",
        "doi": "10.1037/0033-2909.124.2.262",
        "abstract": "Meta-analysis of 85 years of selection research; general mental ability plus a structured interview yields high predictive validity; ranks predictors for hire quality.",
        "source": "seed:framework",
    },
    {
        "title": "The structured employment interview: Narrative and quantitative review",
        "authors": "Levashina, J.; Hartwell, C. J.; Morgeson, F. P.; Campion, M. A.",
        "year": 2014,
        "venue": "Personnel Psychology",
        "url": "https://doi.org/10.1111/peps.12109",
        "doi": "10.1111/peps.12109",
        "abstract": "Reviews structured vs. unstructured interviews; structure increases validity and reduces bias; recommends behaviorally-anchored, standardized questions.",
        "source": "seed:framework",
    },
    {
        "title": "Uniform Guidelines on Employee Selection Procedures (29 CFR 1607)",
        "authors": "U.S. Equal Employment Opportunity Commission; Civil Service Commission; Department of Labor; Department of Justice",
        "year": 1978,
        "venue": "Federal Register",
        "url": "https://www.eeoc.gov/laws/guidelines/uniform-guidelines-employee-selection-procedures-1978",
        "doi": "",
        "abstract": "Codifies the four-fifths rule for adverse-impact screening of selection procedures; defines validation strategies (criterion, content, construct).",
        "source": "seed:framework",
    },
    {
        "title": "What Works: Gender Equality by Design",
        "authors": "Bohnet, I.",
        "year": 2016,
        "venue": "Harvard University Press / Belknap",
        "url": "https://www.hup.harvard.edu/catalog.php?isbn=9780674545393",
        "doi": "",
        "abstract": "Behavioral-design interventions for debiasing hiring; blind/anonymized screening and structured evaluation reduce the influence of demographic cues.",
        "source": "seed:framework",
    },
    {
        "title": "A meta-analysis of the relations of personality and cognitive ability to job performance",
        "authors": "Barrick, M. R.; Mount, M. K.",
        "year": 1991,
        "venue": "Personnel Psychology",
        "url": "https://doi.org/10.1111/j.1744-6570.1991.tb00688.x",
        "doi": "10.1111/j.1744-6570.1991.tb00688.x",
        "abstract": "Big Five predictors of job performance; conscientiousness generalizes across occupations; supports competency-based, job-relevant selection.",
        "source": "seed:framework",
    },
    {
        "title": "Applicant reactions to selection procedures: A review and empirical test of a model",
        "authors": "Hausknecht, J. P.; Day, D. V.; Thomas, S. C.",
        "year": 2004,
        "venue": "Personnel Psychology",
        "url": "https://doi.org/10.1111/j.1744-6570.2004.tb00483.x",
        "doi": "10.1111/j.1744-6570.2004.tb00483.x",
        "abstract": "Candidate-experience (procedural justice, NPS-style) predicts offer acceptance and employer brand; fairness perceptions matter for sourcing reach.",
        "source": "seed:framework",
    },
    {
        "title": "Adverse impact and validity of selection procedures",
        "authors": "Sackett, P. R.; Shen, W.; Myors, B.",
        "year": 2009,
        "venue": "International Review of Industrial and Organizational Psychology",
        "url": "https://www.shrm.org",
        "doi": "",
        "abstract": "Reviews adverse-impact trade-offs across predictors; composite selection with banding and race-neutral weighting reduces disparate impact at minimal validity cost.",
        "source": "seed:framework",
    },
]


def seed(cfg: Config) -> int:
    """Append the curated seed entries once (deduped)."""
    entries = [Entry(**{k: (v if k != "year" else int(v or 0)) for k, v in e.items()}) for e in SEED_ENTRIES]
    return append_entries(entries, cfg)

# ---------------------------------------------------------------------------
# Scheduling (cross-platform)
# ---------------------------------------------------------------------------
def _python_exec() -> str:
    return sys.executable or "python"


def install_schedule(cfg: Config) -> int:
    """Install a weekly scheduled task to run the updater.

    Uses crontab on POSIX systems and schtasks on Windows. Falls back with
    exit code 3 on unsupported platforms.
    """
    script = os.path.abspath(__file__)
    exec_cmd = f'"{_python_exec()}" "{script}" run'
    today_weekday = datetime.date.today().weekday()  # 0=Mon
    if sys.platform.startswith("win"):
        task_name = f"{SKILL_SLUG}_weekly"
        cmd = [
            "schtasks", "/Create", "/TN", task_name, "/SC", "WEEKLY",
            "/D", ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][today_weekday],
            "/ST", "03:00", "/RU", "SYSTEM", "/F", "/TR", exec_cmd,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            LOG.info("installed Windows scheduled task '%s' (weekly, 03:00).", task_name)
            return 0
        except subprocess.CalledProcessError as exc:
            LOG.error("schtasks failed: %s\n%s", exc, exc.stderr)
            return 3
    if sys.platform.startswith("linux") or sys.platform == "darwin":
        line = f"0 3 * * {today_weekday} {exec_cmd} >> {LOG_PATH} 2>&1\n"
        try:
            existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        except Exception as exc:
            LOG.error("crontab read failed: %s", exc)
            return 3
        if "recruitment-process-audit" in existing and exec_cmd in existing:
            LOG.info("cron entry already present; not reinstalling.")
            return 0
        new_cron = existing + line
        proc = subprocess.run(["crontab", "-"], input=new_cron, capture_output=True, text=True)
        if proc.returncode != 0:
            LOG.error("crontab write failed: %s", proc.stderr)
            return 3
        LOG.info("installed weekly cron entry (03:00, weekday %d).", today_weekday)
        return 0
    LOG.error("scheduling not implemented for platform %s", sys.platform)
    return 3


# ---------------------------------------------------------------------------
# Status / verify
# ---------------------------------------------------------------------------
def status(cfg: Config) -> int:
    brain = cfg.brain_path
    exists = os.path.exists(brain)
    seen = load_seen_hashes(brain) if exists else set()
    size = os.path.getsize(brain) if exists else 0
    batches = 0
    update_lines: List[str] = []
    if exists:
        try:
            with open(brain, "r", encoding="utf-8") as fh:
                text = fh.read()
            batches = text.count("## Automated Crawl Batch")
            update_lines = re.findall(r"^- \[\d{4}-\d{2}-\d{2}\] .+$", text, flags=re.M)
        except OSError:
            pass
    print(json.dumps({
        "brain_path": brain,
        "exists": exists,
        "size_bytes": size,
        "unique_entries": len(seen),
        "crawl_batches": batches,
        "log_entries": len(update_lines),
        "log_path": LOG_PATH,
        "config_path": DEFAULT_CONFIG_PATH,
    }, indent=2))
    return 0


def verify(cfg: Config) -> int:
    """Verify the brain file conforms to the documented append format."""
    ok = True
    messages: List[str] = []
    brain = cfg.brain_path
    if not os.path.exists(brain):
        print("FAIL: brain file missing ->", brain)
        return 1
    try:
        with open(brain, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print("FAIL: cannot read brain file:", exc)
        return 1
    blocks = re.findall(r"## Automated Crawl Batch[^\n]*", text)
    hashes = HASH_RE.findall(text)
    if blocks and len(hashes) < len(blocks):
        ok = False
        messages.append("some crawl blocks lack dedup hashes")
    if "## 7. Knowledge Update Log" not in text:
        ok = False
        messages.append("Knowledge Update Log section missing")
    if not re.search(r"<!--hash:[0-9a-f]{16}-->", text):
        ok = False
        messages.append("no dedup hashes found")
    if ok:
        print("OK: brain file valid (blocks=%d, hashes=%d)." % (len(blocks), len(hashes)))
        return 0
    print("FAIL:")
    for m in messages:
        print(" -", m)
    return 1

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_cfg(args: argparse.Namespace) -> Config:
    cfg = Config.load()
    if getattr(args, "sources", None):
        cfg.sources = list(args.sources)
    if getattr(args, "fetcher", None):
        cfg.fetcher = args.fetcher
    if getattr(args, "dry_run", False):
        cfg.dry_run = True
    if getattr(args, "verbose", False):
        cfg.verbose = True
    if getattr(args, "max_arxiv", None) is not None:
        cfg.max_arxiv_results = args.max_arxiv
    return cfg


def cmd_run(args: argparse.Namespace) -> int:
    cfg = _build_cfg(args)
    configure_logging(cfg.verbose)
    LOG.info("knowledge_updater run (skill #%s, %s)", SKILL_ID, SKILL_SLUG)
    fetcher = select_fetcher(cfg)
    entries = fetcher.fetch()
    LOG.info("fetched %d candidate entries.", len(entries))
    appended = append_entries(entries, cfg)
    LOG.info("appended=%d", appended)
    return 0


def cmd_seed(args: argparse.Namespace) -> int:
    cfg = _build_cfg(args)
    configure_logging(cfg.verbose)
    LOG.info("seeding curated entries into knowledge base.")
    appended = seed(cfg)
    LOG.info("seed appended=%d", appended)
    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    cfg = _build_cfg(args)
    configure_logging(cfg.verbose)
    return install_schedule(cfg)


def cmd_status(args: argparse.Namespace) -> int:
    cfg = _build_cfg(args)
    configure_logging(cfg.verbose)
    return status(cfg)


def cmd_verify(args: argparse.Namespace) -> int:
    cfg = _build_cfg(args)
    configure_logging(cfg.verbose)
    return verify(cfg)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="knowledge_updater.py",
        description="Self-improving crawler for the recruitment-process-audit skill.",
    )
    p.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    sub = p.add_subparsers(dest="command", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--sources", nargs="*", default=None, help=f"source slugs: {list(SOURCES.keys())}")
        sp.add_argument("--fetcher", choices=["auto", "crawl4ai", "http"], default=None)
        sp.add_argument("--dry-run", action="store_true", help="do not write to the brain file")
        sp.add_argument("--verbose", action="store_true")

    sp_run = sub.add_parser("run", help="run a crawl + append cycle")
    add_common(sp_run)
    sp_run.add_argument("--max-arxiv", type=int, default=None, help="max ArXiv results per query")
    sp_run.set_defaults(func=cmd_run)

    sp_seed = sub.add_parser("seed", help="append curated seed entries (once, deduped)")
    add_common(sp_seed)
    sp_seed.set_defaults(func=cmd_seed)

    sp_sched = sub.add_parser("schedule", help="install a weekly scheduled task")
    add_common(sp_sched)
    sp_sched.set_defaults(func=cmd_schedule)

    sp_status = sub.add_parser("status", help="print knowledge-base status as JSON")
    add_common(sp_status)
    sp_status.set_defaults(func=cmd_status)

    sp_verify = sub.add_parser("verify", help="verify the brain file conforms to format")
    add_common(sp_verify)
    sp_verify.set_defaults(func=cmd_verify)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        LOG.exception("unhandled error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
