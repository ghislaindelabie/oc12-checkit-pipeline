# OC12 / CheckIt.AI — Implementation plan

*Last update: 2026-06-05. Status of record: [PROJECT_STATUS.md](PROJECT_STATUS.md).
Decisions of record: [research/06-implementation-blueprint.md](research/06-implementation-blueprint.md) §8.*

The five graded OC deliverables map onto seven development phases. Each phase is
gated by tests (TDD) and, where it touches the outside world, by a live smoke run.

## Phase map

| # | Phase | Graded deliverable | Status |
|---|---|---|---|
| 0 | Research, source qualification, decisions | feeds Step 1 | ✅ done |
| 1 | Extraction layer (live connectors) | **Step 2** | ✅ code done; live validation: RSS/Bluesky/Guardian ✅, GDELT query tuning ◐, 6 APIs await keys ⬜ |
| 2 | Corpus layer (labeled datasets + fact-check) | **Step 2** (+ feeds Step 1 evidence) | 🔄 in progress |
| 3 | Step 1 report writing (French) | **Step 1** | ⬜ next after corpus screens |
| 4 | Transform pipeline + conceptual schema | **Step 3** | ✅ done (999,992 rows, valid 97.8%) |
| 5 | Airflow ETL → secured PostgreSQL | **Step 4** | ✅ done (978K rows loaded, 3 DAGs, evidence in deliverables/step4) |
| 6 | KPI dashboard + monitoring plan | **Step 5** | ⬜ |

## Phase detail

### Phase 1 — Extraction layer ✅/◐

Done: `RawRecord` envelope · JSONL storage · RSS (probe + og:image fallback) ·
Bluesky (pseudonymized) · GDELT client · 7 keyed adapters · CLI with `--from/--to`
windowing (Airflow data interval injects here later).

Remaining:
- [ ] GDELT FR query tuning at polite pace (~1 req/30 s) → pin production query
- [ ] Live-validate remaining 6 keyed adapters as keys are registered (5-min fixture fix each if reality differs)

### Phase 2 — Corpus layer 🔄

Done: FakeNewsNet download + load (23,196 records) · image-screen module ·
Fakeddit downloader/loader (raw label ints; semantics resolved in transform) ·
DGM4 downloader.

In flight: FakeNewsNet og:image screen (200-URL stratified sample) · Fakeddit
TSV download · DGM4 10.7 GB snapshot.

Remaining:
- [ ] Read FakeNewsNet screen report → admission decision #7 (gate: usable pairing rate; rot rate becomes a KPI)
- [ ] DGM4 layout inspection → record mapping + loader (+ tests)
- [ ] Fakeddit label-semantics resolution against the paper (2/3/6-way int conventions) — in transform, not raw
- [ ] Fact-check layer: ClaimReview dump (DataCommons) + EUvsDisinfo — dump-preferred rule; Google FCT as query-only illustration script
- [ ] Image binaries: corpus-side image fetcher (Pillow-validated, SHA-256/pHash, `data/images/`), sampled for Fakeddit, full for screened FakeNewsNet subset

### Phase 3 — Step 1 report (French) ✅ v1 written

`deliverables/step1/rapport-exploration-sources.md` (2026-06-05): méthodologie
5 axes · architecture 3 couches · tableau comparatif (11 sources, volumes
mesurés) · écartées-et-pourquoi (8 refus motivés) · cas Wardle · enveloppe
RawRecord (champs indispensables) · formats JSONL→Parquet · opinion/satire/
désinformation · choix de conception transverses. Remaining: refresh numbers
once fact-check layer lands; owner proofread before hand-in.

### Phase 4 — Transform pipeline + conceptual schema ✅

- `checkit/transform/`: lecture (JSONL) → traitement (nettoie_texte, valide_image,
  is_valid_pair, dedup SHA-256/pHash, label normalization incl. Fakeddit semantics
  + satire-class preservation, language detect) → export (Parquet + CSV index).
- RunReport JSON (valid_rate, pairing_rate, dup_rate, per-source counts) — the
  numbers the DAG gate and dashboard consume.
- Conceptual ERD (Mermaid, business-level: PUBLICATION/IMAGE/LABEL/SOURCE) +
  field dictionary → `docs/conceptual_schema.md`. Physical DDL stays in Phase 5
  (conceptual ≠ physical is a graded trap).

### Phase 5 — Airflow ETL → secured PostgreSQL ✅

- PostgreSQL 16 container (compose): `articles` (UNIQUE(url), JSONB extras),
  `pipeline_metrics`; scram-sha-256; `etl_writer`/`dashboard_reader`; pgcrypto
  on one column; psycopg3.
- Astro CLI (Airflow 3.2.x, `airflow.sdk` imports): **three DAGs** — corpus
  `@once`, fact-check dumps `@weekly`, live connectors `@daily`; thin `@task`s
  delegating to the package; XCom carries paths only; quality gate aborts load
  if valid_rate < 0.5; run evidence (UI screenshots + logs) for the deliverable.

### Phase 6 — Dashboard + monitoring ⬜

- Streamlit (FR UI): 4 `st.metric` + 3 charts on précision/rapidité/coût, reading
  `pipeline_metrics` via read-only role, ttl=300, empty-state guard, seed script.
- Monitoring plan (FR, Markdown): seuils / gestion erreurs / fréquence, enforced
  vs observational explicitly mapped to real code; alert stub documented as stub.

## Standing rules

- TDD; suite stays hermetic and <5 s. Live smoke after every external-facing change.
- Conventional commits (EN), feature branches, PRs target `main`, owner merges.
- Bulk data on `/data/files/OC12`; secrets only in `.env`; binding-clause rule for
  any new source.
- Deliverable language: FR user-facing, EN code.
