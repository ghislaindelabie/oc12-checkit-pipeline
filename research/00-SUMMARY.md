# OC12 — Preliminary Research Summary

*Synthesis of the five research reports for the CheckIt.AI multimodal data-acquisition pipeline. Read this first; each section links to the deep report behind it.*

## The mission, restated

You are a junior Data Engineer at **CheckIt.AI**, a (French) startup building automated misinformation / fake-news detection. The job is to build a **robust, modular, autonomous Python pipeline** that acquires **multimodal data — text + image *paired in the same record*** — from a source of your choice, transforms it into a clean ML-ready dataset, orchestrates the flow with **Airflow** into a secured DB, and exposes pipeline **KPIs on a Streamlit dashboard** with a monitoring plan.

The lead technique's audio confirms the spirit: *one robust, clear, modular script that runs without manual intervention*, from News API / Reddit / Open Data / an allowed-to-scrape site.

**The single most important non-obvious idea across all reports:** the value of this project is the **text↔image pairing integrity** and **label quality** — not the volume of rows. Treat "is the image actually present, downloadable, and bound to this text?" as a first-class, measured property.

## Reports in this folder

| # | Report | What it answers |
|---|--------|-----------------|
| 01 | [Project Strategy](01-project-strategy.md) | End-to-end approach, target architecture, roadmap, success criteria, pitfalls |
| 02 | [Data Sources](02-data-sources.md) | 24 sources qualified; ranked shortlist for the pipeline |
| 03 | [Domain & Legal](03-domain-and-legal.md) | Multimodal detection field, label reliability, EU/FR legal & ethical limits, required fields |
| 04 | [Orchestration & Monitoring](04-orchestration-and-monitoring.md) | Airflow setup, DB choice, KPIs, Streamlit, monitoring plan |
| 05 | [Tools & Techniques](05-tools-and-techniques.md) | Concrete extraction technique + library stack per source |

---

## Cross-cutting conclusions

### 1. Source strategy — one live feed + labeled corpora

The two research angles (sources + domain) converge on a layered choice rather than a single source:

- **Live pipeline feed → NewsData.io API.** `image_url` is a first-class field, free tier ~2000 articles/day, commercial use allowed, 89 languages, clean REST/JSON. This is what the *automated* pipeline (Steps 2-4) actually runs on. **Currents API** is the drop-in fallback.
- **Labeled training/validation corpora → Fakeddit + FakeNewsNet.** Fakeddit (1M+ paired image+text posts, distant-supervision labels, pre-split) is the bulk; FakeNewsNet (PolitiFact/GossipCop, human fact-checker labels) is the high-quality smaller set.
- **Held-out evaluation → MMFakeBench** (ICLR 2025, 12 manipulation subtypes, CC BY 4.0).

> ⚠️ **Tension to resolve before building:** the brief asks for an *automated extraction script* that "runs without intervention" — that points at a **live API (NewsData.io)**. But the live API has **no true/fake labels**. The labeled value lives in the **static datasets**. Report 01 recommends NewsData.io as the single primary live source and applying **source-level reliability labels (MBFC factuality axis)** as weak supervision. Report 02 recommends building the *dataset* on Fakeddit/FakeNewsNet. **These are two valid project shapes — pick one as the spine (see "Decision needed" below).**

### 2. Domain → schema. What you MUST extract

Multimodal detectors key on **text–image (in)consistency**, manipulated/AI-generated images, and out-of-context reuse. That dictates the indispensable fields per record:

`id` · `text` (title + body) · `caption` · `image_url` (+ stored path/bytes only if license permits) · `image_hash` (SHA-256 + perceptual pHash) · `label` · **`label_source`** · **`label_confidence`** · `publish_date` · `source_domain` · `url` · `language` · **`license` / usage flag** · `paired_ok` (validation flag) · optional `ambiguous` flag.

### 3. The opinion-vs-disinformation line is a scoring lever, not a footnote

The brief warns against it twice; reports 01 and 03 both flag it as the most common junior failure.
- **Disinformation** = objectively false, spread intentionally to deceive.
- **Controversial opinion** = subjective, divisive, but protected speech. **Satire ≠ disinformation either** — keep satire as its own class.
- **Operationally:** label only verifiable factual claims; use a fact-check *factuality* axis, **never a political-bias axis**; flag borderline cases with `ambiguous` rather than silently collapsing them.

### 4. Legal posture (CheckIt.AI is French → EU/FR law applies)

- **Prefer official APIs and openly-licensed datasets.** Scraping is the explicit last resort.
- **Scraping French sites carries criminal exposure**: bypassing robots.txt / CAPTCHAs repeatedly can be a STAD offence (Art. 323-1 Code Pénal). Log `robots_txt_allows` and obey it in code (`urllib.robotparser`).
- **EU TDM Art. 4 opt-out** blocks commercial training on opt-out publishers (AFP, Reuters, Le Monde…). Rely on open-licensed datasets + officially distributed research corpora.
- **Never redistribute raw copyrighted images.** Store URL + hash (+ embedding); store binaries only under a permissive license.

### 5. Architecture & stack (Steps 2-5)

```
NewsData.io API ─┐
Fakeddit TSV ────┼─► extract/  ─► raw JSONL  ─► transform/ ─► clean Parquet ─► load/ ─► PostgreSQL
FakeNewsNet ─────┘   (modular)    (on disk)     (clean,        (training-      (+ images on
RSS (fallback)                                   dedup, pair,    ready)          disk / MinIO)
                                                 label-join)
        every step = a distinct Airflow PythonOperator/@task; metrics → pipeline_metrics table → Streamlit
```

- **Airflow:** 2.10 via **Astro CLI** (`astro dev start`); TaskFlow `@task`; pass **file paths** through XCom, never image/text payloads; daily schedule, `catchup=False`.
- **Storage:** **PostgreSQL 16** (one row/article, JSONB metadata, `pipeline_metrics` table, read-only `dashboard_reader` role) + **images on filesystem/MinIO referenced by path** — never BYTEA. Security: `scram-sha-256`, least-privilege roles, `pgcrypto`, creds as Airflow Connections.
- **Two schemas, clearly separated** (a known evaluator trap): a **conceptual** model (Mermaid ERD, business meaning) *and* the **physical** DDL — do not conflate them.
- **Core library stack:** `httpx`/`requests` + `tenacity` (retry/backoff), `newsdataapi` SDK, `feedparser`, `trafilatura` (text extraction), `Pillow` + `imagehash` (image validate + dedup), `pydantic-settings` + `SecretStr` (config), JSON structured logging, `pyarrow` (Parquet), `pytest` + `responses`/`vcrpy` (tests). Brief explicitly names requests/BeautifulSoup/Selenium/Scrapy/feedparser — keep those visible; add the modern ones where they clearly win.
- **KPIs (3 axes):** *quality* — valid-record rate (>85%), **image-pairing rate (>70%)**, duplicate rate (<5%), label coverage; *speed* — DAG runtime, per-task duration, records/min; *cost* — API calls vs daily quota, storage size. Written to `pipeline_metrics` at end of load.
- **Streamlit:** `st.metric()` cards + Plotly trends, reads PostgreSQL via `@st.cache_data(ttl=300)`, plain-language labels for non-technical readers.
- **Monitoring:** `retries=3` exponential backoff, `dagrun_timeout`, `on_failure_callback` → Slack, a **data-quality gate** that aborts the load if valid-rate drops below threshold (optionally Great Expectations).

### 6. What "good" looks like (success criteria distilled)

1. **Modularity** — separate `extractor/ transformer/ loader/` packages, functions per concern (connection/parsing/cleaning/saving), config-driven.
2. **Reproducibility & logging** — idempotent loads (`ON CONFLICT DO NOTHING`), structured logs, journaled transformations.
3. **Robustness** — try/except, retries/backoff, quota handling, timeouts.
4. **Legality & label quality** — documented source rights; `label_source`/`label_confidence`; opinion/satire/disinfo distinction explicit.
5. **Pairing integrity** — `paired_ok` measured and reported as a headline KPI.
6. **Clear deliverables** — conceptual schema ≠ physical DDL; working local Airflow DAG with run evidence; non-technical-readable dashboard; monitoring plan aligned to the automation.

---

## Mapping research → the 5 graded deliverables

| Step / Deliverable | Backed by |
|--------------------|-----------|
| **1. Source exploration report** | 02 (sources table + shortlist), 03 (label quality, legal, required fields) |
| **2. Extraction scripts** | 05 (per-source technique + library stack), 01 (modular architecture) |
| **3. Transformation pipeline + conceptual schema** | 05 (cleaning/dedup/pairing/serialization), 03 (required fields), 01 (conceptual-vs-physical) |
| **4. Airflow ETL → secured DB** | 04 (Airflow setup, DB choice, security) |
| **5. KPI dashboard + monitoring plan** | 04 (KPIs, Streamlit, monitoring) |

---

## Decision needed before Step 1 write-up

**Which source is the spine of the *automated pipeline*?**

- **Option A — Live API (NewsData.io) as the spine.** Best fit for "autonomous script that runs on a schedule"; demonstrates real API/quota/retry engineering and live multimodal pairing. *Cost:* no ground-truth labels → use weak source-level (MBFC factuality) labels and document the limitation. *(Report 01's recommendation.)*
- **Option B — Labeled dataset (Fakeddit) as the spine.** Best fit for "dataset to train a detector" with real labels and guaranteed pairing. *Cost:* it's a static download, so the "autonomous extraction" story is weaker — you'd frame the script as ingestion + image resolution + validation. *(Report 02's recommendation.)*
- **Option C — Hybrid (recommended).** NewsData.io as the live, scheduled extraction the Airflow DAG actually runs (satisfies "autonomous"), **plus** Fakeddit/FakeNewsNet as the labeled corpora for the dataset/eval story (satisfies "label quality"). More work, strongest submission.

I'd recommend **Option C**, scoped to NewsData.io + Fakeddit as the two concrete sources, with RSS as the demonstrable fallback. Confirm and I'll proceed to the Step 1 source-exploration report.
