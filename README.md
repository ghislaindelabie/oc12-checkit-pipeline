# CheckIt.AI — Pipeline d'acquisition de données multimodales

## Pourquoi ce projet

**CheckIt.AI** développe un moteur de détection automatique de désinformation. Les
détecteurs modernes ne lisent pas que le texte : ils exploitent la **cohérence (ou
l'incohérence) entre le texte et l'image** d'une publication — image authentique sortie
de son contexte, photo manipulée, légende qui contredit l'image. Leur matière première
doit donc être des publications où **texte et image sont appariés dans le même
enregistrement**, accompagnées d'un **label de véracité fiable**.

Ce dépôt est le **pipeline d'ingénierie de données** qui produit cette matière première :
il acquiert des publications multimodales depuis une douzaine de sources, les normalise
vers un schéma commun, les charge dans une base sécurisée, et en expose les indicateurs
qualité — le tout orchestré et reproductible.

> Projet de formation AI Engineer (non commercial). Les droits de chaque source sont
> évalués sur le **document contraignant** (CGU, licence, robots.txt), jamais sur le
> discours marketing ; les images sont conservées localement et **jamais redistribuées**.

## Ce que fait le pipeline

1. **Extraire** des publications (texte + image) depuis 13 sources hétérogènes, chacune
   derrière un adaptateur qui traduit son dialecte vers une **enveloppe commune**
   (`RawRecord`) — couche brute en JSONL.
2. **Transformer** : nettoyage, normalisation des labels de 6 taxonomies vers
   `{real, fake, satire, unverified}`, qualification de l'appariement texte↔image,
   déduplication — couche propre en Parquet + index CSV, avec un rapport de KPI.
3. **Charger** dans **PostgreSQL 16** sécurisé, de façon **idempotente** (re-jouable sans
   doublon), derrière une porte de qualité.
4. **Orchestrer** avec **Apache Airflow 3.2** : trois DAGs aux cadences distinctes.
5. **Visualiser** les KPI sur un tableau de bord **Streamlit** + plan de monitoring.

```
Corpus annotés      DGM4 · Fakeddit · FakeNewsNet        ─┐  DAG @once
Fact-checking       ClaimReview · EUvsDisinfo · Google FCT ─┤  DAG @weekly
APIs presse + RSS   GDELT · Guardian(+6) · presse FR · satire ─┼─ extract ─► JSONL brut
Réseau social       Bluesky                                ─┘  DAG @daily      │
                                                                       transform ─► Parquet + index CSV
                                                                              │
                                       load (idempotent) ─► PostgreSQL 16 sécurisé + images sur disque
                                                                              │
                                     Streamlit : KPI (appariement · validité · rapidité · coût)
```

## Sources de données collectées

Trois couches complémentaires : les **corpus annotés** portent les labels (vérité
terrain), le **fact-checking** fournit une source de vérité réutilisable, les
**connecteurs live** démontrent l'acquisition automatisée. Chiffres = enregistrements
distincts et valides en base (~1,02 M au total).

| Source | Type | Rôle | Labels (provenance · confiance) | En base |
|---|---|---|---|---:|
| **DGM4** | corpus | manipulations image/texte localisées | synthétiques exacts · 1,0 | 230 000 |
| **Fakeddit** | corpus | plus grand corpus multimodal | supervision distante · 0,6 | 677 491 |
| **FakeNewsNet** | corpus | labels fact-checkers humains | PolitiFact/GossipCop · 0,9 | 23 196 \* |
| **ClaimReview** | fact-check | verdicts mondiaux + URLs de jonction | fact-checkers IFCN · 0,9 | 70 667 |
| **EUvsDisinfo** | fact-check | narratifs pro-Kremlin FR/UE | analystes UE · 0,9 | 18 249 \* |
| **Webz fake-news** | live « fake » | seule source live côté fake | site flaggé · 0,5 | 44 712 |
| **GDELT DOC 2.0** | API presse | flux multilingue + image, sans clé | — | live |
| **The Guardian** | API presse | presse anglophone + vignette | — | 31 |
| **+6 APIs presse** | API presse | NewsData, GNews, Currents, Mediastack, TheNewsAPI, World News | — | clés requises |
| **RSS presse FR** | flux | France Info, 20 Minutes, Le Figaro | — | 596 |
| **RSS satire** | flux | Le Gorafi, Nordpresse, The Onion (classe satire dédiée) | satire auto-déclarée · 0,95 | 95 |
| **Bluesky** | réseau social | posts image+texte, auteurs pseudonymisés | — | 4 |
| **Google Fact Check Tools** | API requête | verdicts AFP & co. — **jamais stocké** (CGU) | fact-checkers | requête |

\* FakeNewsNet et EUvsDisinfo : labels chargés, appariement image en cours
d'enrichissement (`og:image`). Décomposition complète et par étape :
[`deliverables/rapport-projet.html`](deliverables/rapport-projet.html).

**Choix de méthode notable —** EUvsDisinfo : le site live est protégé par un challenge
Cloudflare et son robots.txt interdit la recherche/pagination ; plutôt que de contourner
une protection anti-bot, nous utilisons le **miroir ouvert officiel** (Zenodo, CC-BY-4.0).

## Démarrage

```bash
uv sync
cp .env.example .env        # clés API optionnelles — voir docs/api-keys.md
uv run python -m pytest tests/ -v --tb=short
```

Extraction (les sources sans clé fonctionnent immédiatement) :

```bash
uv run python -m checkit.extract --source rss --probe     # rendement image des flux
uv run python -m checkit.extract --source bluesky --query "fake news" --limit 50
uv run python -m checkit.corpus  --dataset dgm4           # corpus annotés
```

Transformation → chargement en base sécurisée :

```bash
uv run python -m checkit.transform                 # → Parquet + run_report.json
docker compose -f docker-compose.db.yml up -d      # PostgreSQL 16 (port 5433)
uv run python -m checkit.load_cli                  # porte qualité → chargement idempotent
```

Orchestration Airflow (UI http://localhost:8081) et tableau de bord (port 8501) :

```bash
cd airflow && astro dev start                      # 3 DAGs : @daily, @weekly, manuel
uv run streamlit run dashboard/app.py --server.port 8501
```

Les données volumineuses (JSONL brut, Parquet, images, corpus) sont écrites sous
`CHECKIT_DATA_ROOT` (défaut `/data/files/OC12`), **jamais dans le dépôt**.

## Structure

```
src/checkit/
  config.py            réglages (pydantic-settings, secrets via .env)
  schema.py            RawRecord — enveloppe commune à toutes les sources
  storage.py           écriture JSONL atomique par source et par date
  lang.py              normalisation des codes de langue
  extract/             connecteurs live : GDELT, Bluesky, RSS (+ sonde), 7 APIs presse, throttle
  corpus/              téléchargeurs : DGM4, Fakeddit, FakeNewsNet, ClaimReview, Webz, EUvsDisinfo (+ enrichissement)
  transform/           lecture → traitement (nettoyage, labels, appariement, dédup) → export
  load.py              chargement PostgreSQL idempotent + métriques
  factcheck_query.py   client Google Fact Check Tools (requête seule, sans stockage)
db/                    schéma physique SQL + rôles (sécurité)
dags/ (airflow/)       3 DAGs Airflow 3.2 (Astro CLI)
dashboard/             tableau de bord Streamlit + requêtes KPI testables
tests/                 suite pytest hermétique (132 tests, aucun appel réseau)
research/              qualification des 86 sources, vérifications de licences, blueprint
docs/                  clés API, schéma conceptuel, plan de monitoring, limites de débit
deliverables/          livrables par étape + rapport de projet HTML
```

## Avancement — tous les livrables réalisés

- [x] **Étape 1** — Exploration des sources (86 examinées, droits vérifiés sur pièces) → `deliverables/step1/`
- [x] **Étape 2** — Extraction modulaire : 13 sources, validées en conditions réelles
- [x] **Étape 3** — Transformation + schéma conceptuel (≈ 1,06 M lignes, validité 96 %, appariement déclaré 97 %)
- [x] **Étape 4** — ETL Airflow 3.2 → PostgreSQL 16 sécurisé (~1,02 M en base, idempotence prouvée, scram-sha-256 + rôles + pgcrypto) → `deliverables/step4/`
- [x] **Étape 5** — Dashboard KPI Streamlit + plan de monitoring → `dashboard/`, `docs/plan-monitoring.md`
- [x] Rapport de projet complet → `deliverables/rapport-projet.html`

Finitions restantes : captures UI Airflow (preuve d'exécution), enrichissement image
complet de FakeNewsNet, réglage de la requête FR de GDELT, enregistrement des clés
d'APIs presse restantes (le pipeline tourne déjà sans elles). Détail dans
[`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md).
