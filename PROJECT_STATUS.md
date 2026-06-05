# OC12 / CheckIt.AI — Project status

*Last update: 2026-06-05. Companion doc: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) (step-by-step plan and what's next). Decisions of record: [research/06-implementation-blueprint.md](research/06-implementation-blueprint.md) §8.*

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
| Fact-check aggregators (ClaimReview dump, EUvsDisinfo) | ⬜ next |

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
| `processed/fakenewsnet_screen.json` | image-rot screen report (decision #7 evidence) |
| `corpora/fakenewsnet/` | 4 source CSVs (~44 MB) |
| `corpora/fakeddit/` | multimodal + all TSVs (~60 MB) |
| `corpora/dgm4/` | full HF snapshot (10 GB: metadata JSONs + image zips) |

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
