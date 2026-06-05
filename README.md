# CheckIt.AI — Pipeline d'acquisition de données multimodales

Pipeline Python d'acquisition, transformation et chargement de publications d'actualité **multimodales (texte + image appariés)** pour l'entraînement d'un détecteur de fake news. Projet de formation AI Engineer (OC12).

## Architecture (vue d'ensemble)

```
Corpus annotés (DGM4, Fakeddit, FakeNewsNet)  ──┐  DAG @once
Dumps fact-checking (ClaimReview, EUvsDisinfo) ──┤  DAG @weekly      ┌─ PostgreSQL 16 (sécurisé)
APIs presse (GDELT, NewsData, Guardian, …)     ──┼─ extract → JSONL ─┼─ transform → Parquet ─ load ─┤
Flux RSS (presse FR + satire)                  ──┤  DAG @daily       └─ images → /data/files/OC12/
Social (Bluesky)                               ──┘
                                    Orchestration : Apache Airflow 3.2 (Astro CLI)
                                    KPIs : Streamlit (taux d'appariement, validité, durées, quotas)
```

- **Code** : ce dépôt (`src/checkit/`, `dags/`, `dashboard/`, `tests/`).
- **Données** : `/data/files/OC12/` (disque secondaire) — brut JSONL, Parquet, images, corpus, volume PostgreSQL. Jamais dans git.
- **Décisions d'implémentation** : `research/06-implementation-blueprint.md` (§8 = décisions verrouillées).

## Démarrage

```bash
uv sync
cp .env.example .env   # renseigner les clés API
uv run pytest tests/ -v --tb=short
```

## Livrables (5 étapes)

| Étape | Livrable | Emplacement |
|---|---|---|
| 1 | Rapport d'exploration des sources | `deliverables/step1/` |
| 2 | Scripts d'extraction automatisée | `src/checkit/extract/` |
| 3 | Pipeline de transformation + schéma conceptuel | `src/checkit/transform/`, `docs/` |
| 4 | DAG Airflow ETL → PostgreSQL sécurisé | `dags/` |
| 5 | Dashboard KPI Streamlit + plan de monitoring | `dashboard/`, `docs/` |
