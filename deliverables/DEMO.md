# Guide de démonstration — CheckIt.AI

Tout tourne sur le P710. **Accès direct depuis le portable via le réseau Tailscale**
(aucun tunnel SSH nécessaire — réseau privé chiffré, accessible uniquement à vos appareils) :

| Surface | URL Tailnet |
|---|---|
| **Airflow** ⭐ | **https://p710.tail3089b5.ts.net:8443** |
| **Streamlit** | **http://p710.tail3089b5.ts.net:8501** (ou `http://100.127.169.14:8501`) |

> Airflow est exposé via `tailscale serve` (HTTPS, tailnet uniquement). Streamlit écoute
> sur `0.0.0.0:8501`, donc joignable directement par le nom MagicDNS ou l'IP tailnet.
> Si Airflow redémarre et change de port local, ré-exécuter :
> `tailscale serve --bg --https=8443 http://127.0.0.1:<nouveau_port>`
> (trouver le port : `docker ps | grep api-server`).

La base PostgreSQL et les démos CLI se font **sur le P710** (SSH), pas besoin de les exposer.

## Surfaces démontrables (4)

### 1. Interface Airflow — l'orchestration ETL (livrable étape 4)
La pièce maîtresse de la démo. URL : **http://localhost:13957**
> Le port est attribué dynamiquement par Astro. Le retrouver :
> `docker ps | grep api-server` → colonne ports `127.0.0.1:<PORT>->8080`.

À montrer :
- La liste des **3 DAGs** et leurs cadences.
- Ouvrir `checkit_live_daily` → vue **Graph** : extract → transform → quality_gate → load,
  toutes vertes.
- L'**historique des runs** + les **logs** d'une tâche (preuve d'exécution).
- Déclencher un run en direct (bouton ▶) et le voir passer au vert.

### 2. Tableau de bord Streamlit — les KPI (livrable étape 5)
URL : **http://localhost:8501**

À montrer : cartes KPI (volume, validité, appariement, durée), répartition des labels,
volumes par source, qualité au fil des exécutions avec le seuil d'arrêt tracé.

### 3. Base PostgreSQL sécurisée (livrable étape 4)
Montrer la sécurité concrètement :
```bash
# accès en rôle LECTURE SEULE (comme le dashboard)
docker exec -it checkit-postgres psql "postgresql://dashboard_reader:<MDP>@localhost:5432/checkit" \
  -c "SELECT raw_source, count(*) FROM articles GROUP BY raw_source ORDER BY 2 DESC;"
# prouver le moindre privilège : une écriture échoue en lecture seule
#   INSERT ... -> ERROR: permission denied for table articles
```

### 4. Démos en ligne de commande (live, sans clé)
```bash
uv run python -m checkit.extract --source rss --probe            # rendement image des flux, en direct
uv run python -m checkit.factcheck_query "vaccin Covid" --lang fr # verdicts AFP en direct (Google FCT)
uv run python -m checkit.extract --source bluesky --query "fake news" --limit 20
```

Et le **rapport de projet** : ouvrir `deliverables/rapport-projet.html` dans le navigateur.

## Tout (re)démarrer

```bash
# 1. Base de données
cd ~/code/AI-engineer-training/OC12
docker compose -f docker-compose.db.yml up -d

# 2. Airflow (Astro)
cd airflow && astro dev start --no-browser && cd ..

# 3. Dashboard
uv run streamlit run dashboard/app.py --server.headless true --server.port 8501
```

État actuel (vérifié) : Postgres ✅, Airflow ✅ (3 DAGs), Streamlit ✅.
