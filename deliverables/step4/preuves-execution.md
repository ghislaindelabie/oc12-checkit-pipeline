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

### Exécution du DAG `checkit_live_daily`

*(complété ci-dessous après le run — sortie `airflow dags trigger` + états des tâches + extraits de logs ; captures de l'UI à réaliser lors de la démo via le tunnel SSH : `ssh -L 8081:localhost:8081 p710` puis http://localhost:8081)*
