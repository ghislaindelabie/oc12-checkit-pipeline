# Régulation des débits d'appel (rate limiting)

Tous les composants qui sortent sur le réseau passent par un **régulateur
partagé** (`checkit/extract/throttle.py`) : une porte par clé (source ou
domaine), à intervalle minimal entre deux requêtes. Deux composants visant la
même API dans un même processus partagent la même porte.

## Intervalles appliqués et leur provenance

| Clé | Intervalle | Limite ÉNONCÉE par le fournisseur | Provenance / statut |
|---|---|---|---|
| `gdelt` | 5,5 s | « one request every 5 seconds » | **Énoncée par l'API elle-même** (message de throttle, constaté en live 2026-06-05 ; les rafales déclenchent une pénalité prolongée) |
| `bluesky` | 1 s | ~3 000 req/5 min (~10/s) sur l'AppView public | Docs AT Protocol ; on reste 10× sous la limite — atténue aussi le WAF qui bloque la pagination rapide depuis des IP serveur |
| `api:newsdata` | 2 s | 30 crédits/15 min en rafale, ~200/jour (offre gratuite) | Docs fournisseur (à confirmer à l'enregistrement de la clé) |
| `api:guardian` | 1 s | 12 appels/s et ~500/jour (offre développeur) | Docs Open Platform — **validée en live** (clé enregistrée) |
| `api:gnews` | 1 s | ~100 req/jour | Conservateur, en attente de validation live |
| `api:currents` | 1 s | ~600 req/jour | Conservateur, en attente de validation live |
| `api:mediastack` | 2 s | ~100 req/mois (très faible quota) | Conservateur, en attente de validation live |
| `api:thenewsapi` | 1 s | ~100 req/jour | Conservateur, en attente de validation live |
| `api:worldnews` | 1 s | ~50 points/jour, ~1 req/s | Docs fournisseur, en attente de validation live |
| `host:<domaine>` (flux RSS + pages article pour `og:image`) | 1 s / domaine | aucune limite énoncée | Politesse standard vis-à-vis des éditeurs |
| `img:<domaine>` (téléchargement d'images, étape transform) | 0,5 s / domaine | aucune limite énoncée | Politesse ; les CDN étant des hôtes distincts, l'impact global est minime |

## Principes

- **Quota journalier ≠ débit instantané** : les quotas (crédits/jour) sont gérés
  séparément par la limite `--limit` par run + la cadence des DAG ; le throttle
  ne gère que l'espacement instantané.
- Chaque valeur « en attente de validation live » sera resserrée ou relâchée à
  la première utilisation réelle avec clé, contre la page de limites du
  fournisseur du moment.
- Les tests neutralisent les intervalles (fixtures `no_throttle`) — la suite
  reste hermétique et rapide.
