# CheckIt.AI — Pipeline d'acquisition de données multimodales

Pipeline Python d'acquisition, de transformation et de chargement de publications
d'actualité **multimodales** — texte et image appariés dans le même enregistrement —
destiné à l'entraînement de détecteurs de désinformation.

Projet de formation AI Engineer (non commercial). Les droits de chaque source sont
évalués sur le **document contraignant** (CGU, licence, robots.txt), jamais sur le
discours marketing ; les images sont conservées localement et ne sont jamais
redistribuées.

## Architecture

```
Corpus annotés (DGM4, Fakeddit, FakeNewsNet)   ─┐  DAG @once
Fact-checking + flux fake (ClaimReview, Webz) ─┤  DAG @weekly
APIs presse (GDELT, NewsData, Guardian, …)     ─┼─ extract ──► JSONL brut
Flux RSS (presse FR + satire)                  ─┤  DAG @daily      │
Bluesky (recherche publique)                   ─┘             transform ──► Parquet + index CSV
                                                                   │
                                              load ──► PostgreSQL 16 (sécurisé) + images sur disque
                                                                   │
                                  Streamlit : KPIs (appariement, validité, durées, quotas)
```

- **Orchestration** : Apache Airflow 3.2 (Astro CLI), trois DAGs aux cadences distinctes.
- **Propriété mesurée de bout en bout** : le taux d'appariement texte↔image
  (`paired_ok`) — une image déclarée n'est comptée que téléchargeable et valide.
- **Étiquettes** : taxonomie native conservée (`fine_grained_label`) + classe
  agrégée `{real, fake, satire, unverified}` — la satire est une classe à part
  entière, jamais confondue avec la désinformation.

## Démarrage

```bash
uv sync
cp .env.example .env        # clés API optionnelles — voir docs/api-keys.md
uv run python -m pytest tests/ -v --tb=short
```

Extraction (les trois sources sans clé fonctionnent immédiatement) :

```bash
uv run python -m checkit.extract --source rss --probe     # teste le rendement image des flux
uv run python -m checkit.extract --source rss
uv run python -m checkit.extract --source gdelt --query "desinformation sourcelang:french"
uv run python -m checkit.extract --source bluesky --query "fake news" --limit 50
```

Transformation puis chargement en base (PostgreSQL 16 sécurisé) :

```bash
uv run python -m checkit.transform                 # → Parquet + run_report.json
docker compose -f docker-compose.db.yml up -d      # base de données (port 5433)
uv run python -m checkit.load_cli                  # porte qualité → chargement idempotent
```

Orchestration Airflow 3.2 (Astro CLI, UI sur http://localhost:8081) :

```bash
cd airflow && astro dev start                      # 3 DAGs : @daily, @weekly, manuel
```

Tableau de bord KPI (lecture seule sur la base) :

```bash
uv run streamlit run dashboard/app.py --server.port 8501
```

Les données (JSONL brut, Parquet, images, corpus) sont écrites sous
`CHECKIT_DATA_ROOT` (par défaut `/data/files/OC12`), jamais dans le dépôt.

## Structure

```
src/checkit/          paquet principal
  config.py           réglages (pydantic-settings, secrets via .env)
  schema.py           RawRecord — enveloppe commune à tous les extracteurs
  storage.py          écriture JSONL atomique par source et par date
  extract/            extracteurs : GDELT, Bluesky, RSS (+ sonde de flux)
tests/                suite pytest hermétique (fixtures, aucun appel réseau)
research/             qualification des sources, vérifications de licences, blueprint
docs/                 documentation projet (clés API, schéma conceptuel à venir)
dags/                 DAGs Airflow (étape 4)
dashboard/            tableau de bord Streamlit (étape 5)
```

## Avancement

- [x] Qualification des sources (86 examinées, licences vérifiées sur pièces)
- [x] Socle : configuration, schéma commun, stockage JSONL
- [x] Extracteurs sans clé : GDELT, Bluesky, RSS (+ fallback `og:image` pour la satire)
- [x] Adaptateurs APIs presse à clé (NewsData, Guardian, GNews, Currents, Mediastack, TheNewsAPI, World News) — code testé sur fixtures, validation live à l'enregistrement des clés
- [x] Corpus annoté FakeNewsNet (23 196 métadonnées + labels PolitiFact/GossipCop)
- [ ] Corpus annotés DGM4 + Fakeddit ; criblage images FakeNewsNet
- [x] Corpus ClaimReview (98 455 verdicts de fact-checkers) + rapport d'exploration (étape 1)
- [x] Pipeline de transformation + schéma conceptuel (999 992 lignes, validité 97,8 %)
- [x] Chargement PostgreSQL 16 sécurisé (978 289 lignes, idempotence prouvée, scram-sha-256 + rôles + pgcrypto)
- [x] DAGs Airflow 3.2 (@daily, @weekly, corpus manuel) via Astro CLI
- [x] Dashboard KPI Streamlit (port 8501) + plan de monitoring
