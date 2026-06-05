# Clés API — checklist d'inscription

Chaque clé est optionnelle : une source sans clé est **ignorée proprement** par le
pipeline (pattern *skip-if-no-key*). Renseigner les clés dans `.env`
(jamais commité — voir `.env.example`).

## Sans inscription (déjà fonctionnels)

| Source | Accès | Limites |
|---|---|---|
| GDELT DOC 2.0 | aucun compte | ~1 requête / 5 s (le client respecte l'intervalle) ; fenêtre glissante ~3 mois ; attribution requise |
| Flux RSS (France Info, 20 Minutes, Le Figaro, Le Gorafi, Nordpresse, The Onion) | aucun compte | politesse standard ; images via flux ou og:image |
| Bluesky (recherche publique) | aucun compte | rate-limits publics généreux ; auteurs pseudonymisés |

## Inscription nécessaire (gratuites)

| # | Service | Inscription | Offre gratuite (indicative — vérifier à l'inscription) | Variable `.env` |
|---|---|---|---|---|
| 1 | NewsData.io | <https://newsdata.io/register> | ~200 crédits/jour, champ `image_url`, filtre FR | `CHECKIT_NEWSDATA_API_KEY` |
| 2 | The Guardian Open Platform | <https://open-platform.theguardian.com/access/> | ~500 appels/jour, archive depuis 1999, `fields=thumbnail` | `CHECKIT_GUARDIAN_API_KEY` *(clé déjà détenue)* |
| 3 | GNews | <https://gnews.io/> | ~100 requêtes/jour, champ `image`, FR | `CHECKIT_GNEWS_API_KEY` |
| 4 | Currents API | <https://currentsapi.services/en/register> | ~600 requêtes/jour, champ `image`, FR | `CHECKIT_CURRENTS_API_KEY` |
| 5 | Mediastack | <https://mediastack.com/signup/free> | ~100 requêtes/mois (faible), champ `image` | `CHECKIT_MEDIASTACK_API_KEY` |
| 6 | TheNewsAPI | <https://www.thenewsapi.com/register> | ~100 requêtes/jour, champ `image_url` | `CHECKIT_THENEWSAPI_API_KEY` |
| 7 | World News API | <https://worldnewsapi.com/> | ~50 points/jour, champ `image` | `CHECKIT_WORLDNEWS_API_KEY` |

**Conseil d'ordre :** 1 et 2 d'abord (les deux adaptateurs les plus utiles : volume FR
+ archive historique) ; 3–7 ensuite, au fil de l'implémentation des adaptateurs.

## Hors APIs presse (plus tard dans le projet)

- **Corpus annotés** (DGM4, Fakeddit, FakeNewsNet) : téléchargements directs,
  pas de clé — liens et licences documentés dans `research/sweep/labeled-datasets.md`.
- **Google Fact Check Tools** (requêtes ponctuelles uniquement, pas de stockage
  permanent — contrainte CGU) : clé Google Cloud gratuite si on l'active,
  décision à prendre au moment du script de requête.
