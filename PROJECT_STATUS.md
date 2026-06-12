# OC12 / CheckIt.AI — Project status

*Last update: 2026-06-05 (evening — transform pipeline landed). Companion doc: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) (step-by-step plan and what's next). Decisions of record: [research/06-implementation-blueprint.md](research/06-implementation-blueprint.md) §8.*

## What this project is

Graded OpenClassrooms AI-engineer mission: as a junior Data Engineer at CheckIt.AI
(fictional French fake-news-detection startup), build a robust, modular, unattended
pipeline acquiring **multimodal news data (text + image paired in one record)** →
transform → Airflow ETL into a secured database → Streamlit KPI dashboard +
monitoring plan. Five graded deliverables, one per mission step.

## Achieved so far

### Phase 0 — Research & decisions (2026-05-29 → 2026-06-05) ✅

- Preliminary research: 5 reports (`research/01..05`) covering strategy, sources,
  legal, orchestration, tooling.
- Multi-agent verification sweep (2026-06-05): **86 sources qualified across 6
  categories**, 13 adversarially verified against their *binding* documents
  (ToS/LICENSE/robots) — not marketing. Full details: `research/sweep/*.md`.
  - Notable: GDELT promoted (clean attribution-only ToS, paired `socialimage`);
    NewsData.io rights formally unverifiable (unreadable ToS); Telegram, Mastodon
    and bulk Google-FactCheck **refuted**; DGM4's real license is S-Lab 1.0
    research-only (HF tag says apache-2.0 — wrong).
- **All 20 implementation decisions locked with the owner** → blueprint §8.
  Spine = **Option D corpus-first**: labeled corpora (the training payload)
  + fact-check aggregators (dump-preferred) + live connectors as ingestion
  illustrations (news APIs, RSS, Bluesky).

### Phase 1 — Extraction layer (2026-06-05) ✅ (live validation partial)

| Component | State | Evidence |
|---|---|---|
| Repo scaffold (uv, py3.12, src layout, pydantic-settings, SecretStr keys, skip-if-no-key) | ✅ merged (#1) | 8 tests |
| `RawRecord` common envelope + JSONL storage on `/data/files/OC12` | ✅ merged (#3) | deterministic ids, UTC, unicode tests |
| RSS extractor (6 feeds, image cascade + `og:image` fallback for satire) | ✅ merged (#3), **live-validated** | probe: franceinfo 31/31, 20minutes 30/30, lefigaro 17/18; satire 0/20 in-feed → 5/5 via fallback; 121 records written |
| Bluesky extractor (public search, image posts only, authors salted-hash pseudonymized) | ✅ merged (#3), **live-validated** | 4 records; WAF-403 mid-pagination handled gracefully |
| GDELT DOC 2.0 client (no key, 5.5 s throttle) | ✅ merged (#3), integration OK | FR query tuning pending (KNOWN_ISSUES) |
| 7 keyed news-API adapters (declarative specs: NewsData, Guardian, GNews, Currents, Mediastack, TheNewsAPI, WorldNews) | ✅ PR #4, fixture-tested | **Guardian live-validated 2026-06-05** (key registered): date windows + thumbnails OK, 7 records. Others await keys |
| Extraction CLI (`--source <name>|keyed|rss --probe`, `--from/--to` window) | ✅ PR #4 | window defaults to last-24h; Airflow will inject its data interval |

### Phase 2 — Corpus layer (2026-06-05) ✅ (fact-check sources remain)

| Component | State |
|---|---|
| FakeNewsNet downloader + loader | ✅ **live: 23,196 labeled records** (politifact 432/624, gossipcop 5,323/16,817 — matches published stats). csv field-limit fix for viral rows |
| FakeNewsNet **image screen** (decision #7 gate) | ✅ **measured on 200-URL stratified sample: 47% og:image yield overall** (gossipcop fake 64% / real 58%; politifact fake 42% / real 24%); 65.5% pages reachable. **Verdict: ADMIT with documented rot** — est. ~10–11K paired records; rot rate becomes a headline KPI; politifact:real is the weak group |
| Fakeddit downloader (Drive TSVs) + loader | ✅ **live: 680,798 multimodal records** (train 562,466 / val 59,169 / test 59,163 — matches the published ~682K subset). Label ints kept raw until transform |
| DGM4 downloader (HF 10.7 GB) + loader | ✅ **live: 281,015 records** (= HF row count) across 9 fine-grained manipulation classes incl. combos; 128,441 orig / 152,574 manipulated; grounding flags kept |
| ClaimReview aggregate dump (DataCommons) | ✅ **live: 98,455 verdicts** from IFCN fact-checkers worldwide, with appearance-URL join surface; ratings kept raw (multilingual). Malformed-date fix |
| EUvsDisinfo | ⏸ 403 from server IPs (KNOWN_ISSUES) — ClaimReview covers the need |
| Webz.io fake-news-dataset (added 2026-06-05 on owner's request) | ✅ qualified + integrated: the only LIVE fake-side source (weekly drops, 94% measured image pairing, ~106K articles since Feb 2025); source-level label at confidence 0.5, ai_allow opt-outs respected, trust.bias never used as label. Full fiche in the Step 1 report |
| EUvsDisinfo (added 2026-06-12 on owner's request) | ✅ integrated via OPEN MIRROR not scraping: live site is Cloudflare-challenged + robots-restricted → used Zenodo CC-BY-4.0 base (18,249 cases: 10,682 disinfo / 7,567 trustworthy), enriched with our trafilatura+og:image stack (sample: 65% text, 45% image). EU-analyst labels at confidence 0.9 — the FR/EU pro-Kremlin narrative signal. Weekly DAG task added |
| Google Fact Check Tools (query-only) | ✅ `factcheck_query` client live-validated (key registered): returns AFP Factuel + others; compliance-by-design (no storage). The query-only route to French verdicts the ClaimReview dump lacks |

### Phase 4 — Transform pipeline (2026-06-05) ✅

| Component | State |
|---|---|
| `checkit/transform/` — lecture / traitement / export stages | ✅ `nettoie_texte`, `text_fingerprint`, label normalization, pairing qualification, dedup, Parquet+CSV export, RunReport JSON |
| Label normalization across 5 taxonomies | ✅ Fakeddit int conventions **pinned empirically** (subreddit crosstab, zero noise); ClaimReview multilingual map (FR/EN/ES/TR/ID/JA/FA/AR top values; 31K tail counted unmapped); confidence ladder 1.0 synthetic > 0.9 human > 0.6 distant |
| Pairing qualification | ✅ `paired_ok` + `pairing_basis` {validated, bundled, declared, none} — strict and declared KPIs reported separately |
| Identity correctness | ✅ two real bugs found by the first full run and fixed with regression tests: DGM4 sample identity = (image+text) — dedup now lands **exactly on the paper's 230,000** (152,574 fake / 77,426 real); ClaimReview identity = (url+claim) |
| **Full live run** | ✅ **1,083,592 raw → 999,992 clean rows** in ~125 s; valid_rate **97.8%**, pairing declared **97.7%**, strict 24.8%; dups removed: 52,472 by id + 31,132 by content |
| Conceptual schema (Mermaid, FR) | ✅ `docs/conceptual_schema.md` — PUBLICATION/IMAGE/LABEL/SOURCE, conceptual ≠ physical |
| Outputs | `processed/dataset.parquet` (~1M rows), `dataset_index.csv`, `run_report.json` |

Known gap: FakeNewsNet records are `pairing_basis=none` until the og:image
enrichment job runs (admitted-with-rot decision #7) → its `is_valid`=0 for now,
by design honesty.

### Phase 5 — Airflow ETL → secured PostgreSQL (2026-06-05) ✅

| Component | State |
|---|---|
| PostgreSQL 16 (dedicated container, port 5433) | ✅ `docker-compose.db.yml` — scram-sha-256 enforced (verified: even local psql needs auth), volume on the secondary drive |
| Physical schema `db/schema.sql` | ✅ `articles` (28 cols, CHECK constraints, partial unique on url, 4 indexes) + `pipeline_metrics`; **distinct from the conceptual model** (graded trap defused) |
| Security (the brief's 3 axes) | ✅ scram-sha-256 · least-privilege roles `etl_writer`/`dashboard_reader` (init script, generated passwords in .env) · pgcrypto: `author_pseudo_enc` encrypted at rest |
| Load step (`checkit/load.py` + CLI) | ✅ psycopg3, batched, ON CONFLICT DO NOTHING; quality gate (ValueError if valid_rate<0.5); metrics → `pipeline_metrics` |
| **Live load evidence** | ✅ **978,289 valid rows inserted**; immediate re-run: **0 inserted / 978,289 skipped — idempotency proven live** |
| Airflow 3.2 via Astro CLI (Runtime 3.2-5) | ✅ project in `airflow/`; port 8081 (8080 taken on P710); package mounted via PYTHONPATH (no rebuild per code change); host-gateway to data Postgres |
| 3 DAGs | ✅ `checkit_live_daily` (@daily: extract→transform→gate→load, window = data interval, XCom = paths only) · `checkit_factcheck_weekly` · `checkit_corpus_once` (manual) |
| Run evidence | `deliverables/step4/preuves-execution.md` (CLI evidence in; DAG-run output appended after first triggered run) |

### Phase 6 — KPI dashboard + monitoring plan (2026-06-05) ✅

| Component | State |
|---|---|
| Streamlit dashboard (`dashboard/app.py`, FR, non-technical wording) | ✅ 4 KPI cards (volume/validité/appariement strict+déclaré/durée+débit) + label donut + per-source bar + quality-over-runs line with the 50% gate threshold drawn; empty-state and DB-down guards; cache ttl 300s |
| Read path | ✅ read-only `dashboard_reader` role; UI-free `dashboard/queries.py` so KPI logic is unit-tested |
| **Live boot verified** | ✅ HTTP 200 on :8501, healthz ok; real data through the read-only role (978K articles: fake 569,637 / real 345,268 / satire 40,135 / unverified 23,249) |
| Monitoring plan (`docs/plan-monitoring.md`, FR) | ✅ seuils / gestion erreurs / fréquences + **enforced-vs-observed status per claim** + Mermaid alert flow; alert stub explicitly documented as not-wired |

### Cross-cutting

- **Method**: TDD throughout (**63 hermetic tests, <1 s**, zero network in tests);
  feature branches + PRs, owner merges; live smoke tests after every component —
  they caught 6 real-world issues unit tests can't (satire feeds shipping no
  images, GDELT's real throttle, Bluesky host + WAF behavior, csv field limit,
  Guardian OK).
- **Data**: everything bulky on the secondary drive `/data/files/OC12/`
  (raw JSONL, corpora, processed, images) — never in git.
- **Rights posture**: per-source binding-clause verification recorded; images
  cached locally, never redistributed; Bluesky authors pseudonymized.

## Current data inventory (`/data/files/OC12/`)

| Path | Content |
|---|---|
| `raw/rss/` | 121 paired live records (FR news + satire) |
| `raw/bluesky/` | 4 paired social records |
| `raw/guardian/` | 7 paired API records |
| `raw/fakenewsnet/` | 23,196 labeled metadata records |
| `raw/fakeddit/` | 680,798 labeled multimodal records |
| `raw/dgm4/` | 281,015 labeled records (synthetic manipulations, grounded) |
| `raw/claimreview/` | 98,455 fact-check verdicts (label-join feed) |
| `processed/dataset.parquet` | **999,992 clean rows** (the ML-ready dataset, v1) |
| `processed/dataset_index.csv` | human-browsable index |
| `processed/run_report.json` | KPIs: valid_rate 0.978, pairing declared 0.977/strict 0.248 |
| `processed/fakenewsnet_screen.json` | image-rot screen report (decision #7 evidence) |
| `corpora/fakenewsnet/` | 4 source CSVs (~44 MB) |
| `corpora/fakeddit/` | multimodal + all TSVs (~60 MB) |
| `corpora/dgm4/` | full HF snapshot (10 GB: metadata JSONs + image zips) |
| `corpora/claimreview/` | 198 MB schema.org dump (@weekly refresh planned) |

## Known issues / risks

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md): GDELT FR-query tuning pending (throttle
penalty escalation); 6 keyed adapters unvalidated until keys; Bluesky pagination
WAF; satire og:image cost (1 GET/entry).

## Documentation map

| Doc | Purpose |
|---|---|
| `README.md` | Public face: architecture, quickstart, progress (FR) |
| `PROJECT_STATUS.md` | This file — what's done, evidence, inventory |
| `IMPLEMENTATION_PLAN.md` | Step-by-step plan, owners of each graded deliverable |
| `KNOWN_ISSUES.md` | Live limitations + workarounds |
| `research/00-SUMMARY.md` → `05` | Preliminary research (May 2026) |
| `research/06-implementation-blueprint.md` | **Decision record** (§8 = the 20 locked choices) |
| `research/sweep/*.md` | Per-category source qualification + ToS verification |
| `docs/api-keys.md` | Key registration checklist (FR) |
