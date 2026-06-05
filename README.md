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
Dumps fact-checking (ClaimReview, EUvsDisinfo) ─┤  DAG @weekly
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
- [ ] Adaptateurs APIs presse à clé (NewsData, Guardian, GNews, …)
- [ ] Téléchargeurs de corpus annotés (DGM4, Fakeddit, FakeNewsNet)
- [ ] Pipeline de transformation + schéma conceptuel
- [ ] DAGs Airflow → PostgreSQL sécurisé
- [ ] Dashboard KPI + plan de monitoring
