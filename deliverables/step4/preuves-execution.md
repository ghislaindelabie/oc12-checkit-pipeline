# Étape 4 — Preuves d'exécution du flux ETL Airflow

**Livrable de l'étape 4** avec : les DAGs (`airflow/dags/`), le schéma physique
(`db/schema.sql`), la sécurisation (`db/init-roles.sh`, scram-sha-256, rôles à
moindre privilège, pgcrypto) et la stack locale (`airflow/`, Astro CLI,
Airflow 3.2 / Runtime 3.2-5).

## Architecture d'orchestration

Trois DAGs, trois cadences — chaque tâche est mince et délègue au paquet
`checkit` testé (94+ tests) ; les XCom ne transportent que des chemins de fichiers :

| DAG | Cadence | Chaîne |
|---|---|---|
| `checkit_live_daily` | `@daily` | extract (RSS+Bluesky+APIs à clé, fenêtre = data interval) → transform → **porte qualité** (échec si valid_rate < 0,5) → load idempotent + métriques |
| `checkit_factcheck_weekly` | `@weekly` | re-télécharge le dump ClaimReview (~98K verdicts) → réémet la couche brute |
| `checkit_corpus_once` | manuel | (re)télécharge + charge FakeNewsNet, Fakeddit, DGM4 — idempotent, pour machine neuve |

## Sécurisation de la base (exigences du brief)

1. **Authentification** : scram-sha-256 imposé (`POSTGRES_INITDB_ARGS`), y compris en local.
2. **Accès par rôles** : `etl_writer` (INSERT/SELECT, identité du DAG) ; `dashboard_reader` (SELECT seul, identité du dashboard) ; mots de passe générés, en `.env` non versionné.
3. **Chiffrement des données sensibles** : `pgcrypto` — colonne `author_pseudo_enc` (pgp_sym_encrypt sur l'identifiant d'auteur déjà pseudonymisé) ; SSL en transit documenté.

## Preuves d'exécution (2026-06-05)

### Chargement initial + idempotence (CLI, identité etl_writer)

```
load: 999992 rows read, 978289 valid to load
load: 978289 inserted, 0 already present (idempotent skip)
metrics recorded (dag_id=manual_first_load)

# Re-exécution immédiate (preuve d'idempotence — ON CONFLICT DO NOTHING) :
load: 0 inserted, 978289 already present (idempotent skip)
metrics recorded (dag_id=manual_rerun)
```

### Exécution du DAG `checkit_live_daily` (run planifié du 2026-06-05)

```
extract_live  success   (échec tentative 1 : permissions du volume — corrigé ;
                         la tentative 2 réussit : retries=3 démontré en conditions réelles)
transform     success   (~4 min — 1,08 M d'enregistrements bruts)
quality_gate  success   (valid_rate 0,978 >= 0,5)
load          success   (après correction du binding réseau de la base — voir ci-dessous)
```

Trois incidents réels rencontrés et corrigés pendant la mise en service — chacun
documenté dans KNOWN_ISSUES.md et désormais couvert :

1. **Permissions du volume de données** : l'utilisateur conteneur (uid 50000)
   ne pouvait pas écrire sur `/data/files/OC12` (propriété de l'utilisateur hôte).
   Le mécanisme de retry d'Airflow a absorbé l'incident : la tâche a réussi à la
   tentative suivante, après ouverture des droits.
2. **Binding réseau de la base** : PostgreSQL n'écoutait que sur 127.0.0.1 —
   inaccessible depuis les conteneurs via host.docker.internal. Ajout du binding
   sur la passerelle du bridge Docker (172.17.0.1), le LAN restant fermé.
3. **Runs manuels sans data interval (spécificité Airflow 3)** :
   `data_interval_start/end` valent None sur un déclenchement manuel — le DAG
   replie désormais sur une fenêtre de 24 h, comme la CLI.
4. **Re-crawl d'un article avec image changée** : même URL d'article, URL
   d'image tournée par l'éditeur → nouvelle identité de contenu mais collision
   sur la contrainte d'unicité d'URL. Le chargement utilise désormais
   `ON CONFLICT DO NOTHING` non ciblé : toute collision d'identité (record_id
   OU url) est ignorée — la première version gagne, le run reste idempotent.

### Table `pipeline_metrics` (alimentée par la tâche load)

```
       dag_id         | rows_loaded | commentaire
----------------------+-------------+--------------------------------------------
 manual_first_load    |      978289 | chargement initial (CLI)
 manual_rerun         |           0 | preuve d'idempotence (re-run immédiat)
 checkit_live_daily   |          62 | run PLANIFIÉ : nouvelles publications du jour
 checkit_live_daily   |           0 | run MANUEL : idempotence au niveau du DAG
 manual_webz_backfill |       44712 | intégration de la source Webz (84K bruts,
                      |             | dédupliqués entre drops hebdo qui se recouvrent)
```

**États finaux des runs** : `scheduled__2026-06-05` → **success** (4/4 tâches) ;
`manual__19:20` → **success** ; `manual__18:45` → failed (antérieur aux correctifs,
conservé comme trace). Total en base : **1 023 063 articles**.

### Captures d'écran UI (à réaliser pour le rendu)

Tunnel depuis le Mac : `ssh -L 8081:localhost:8081 <p710>` puis http://localhost:8081
(vue Graph du DAG vert + historique des runs + log de la tâche quality_gate).
