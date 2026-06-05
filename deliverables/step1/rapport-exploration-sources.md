# Rapport d'exploration des sources de données multimodales

**Projet** : CheckIt.AI — pipeline d'acquisition de données multimodales (texte + image appariés) pour la détection de désinformation.
**Auteur** : Ghislain Delabie — Ingénieur Data junior, CheckIt.AI.
**Date** : 5 juin 2026. **Livrable de l'étape 1** (exploration et qualification des sources).

---

## 1. Contexte et objectif

CheckIt.AI développe un moteur de détection automatique de fake news. Les détecteurs
multimodaux s'appuient sur la **cohérence (ou l'incohérence) entre le texte et l'image**
d'une publication : image authentique sortie de son contexte, image manipulée, légende
contredisant la photo. La matière première doit donc être des publications où texte et
image sont **appariés dans le même enregistrement** — c'est la propriété centrale,
mesurée de bout en bout dans ce projet (champ `paired_ok`, KPI de taux d'appariement).

Ce rapport qualifie les sources candidates, justifie celles retenues, documente les
champs à collecter et les formats de sortie, et expose les choix de conception qui
en découlent.

## 2. Méthodologie de qualification

86 sources ont été examinées dans 6 catégories (APIs presse, réseaux sociaux, corpus
académiques annotés, fact-checking/open data, flux RSS/scraping, archives/agrégateurs).
Chaque source est évaluée sur **5 axes** :

1. **Modalités et appariement** — texte ET image dans le même enregistrement ? Par quel mécanisme exact (nom du champ) ?
2. **Format et méthode d'extraction** — API REST, flux RSS, TSV/JSON à télécharger ; bibliothèque adaptée.
3. **Langue** — français prioritaire pour les flux (contexte CheckIt.AI), anglais accepté pour les corpus annotés.
4. **Qualité des labels** — existence d'un label vrai/faux, et surtout sa **provenance** : fact-checker humain > supervision distante > synthétique ; absence de label = `unverified`.
5. **Droits d'usage** — jugés exclusivement sur le **document contraignant** (CGU, fichier LICENSE, robots.txt), jamais sur le discours marketing. Citation de la clause à l'appui. Cadre : exercice de formation **non commercial**.

Pour les sources à fort enjeu, une **contre-vérification adversariale** a été menée
(lecture effective des CGU, test de vivacité, confirmation du champ d'appariement) —
13 sources vérifiées sur pièces. Enfin, chaque source intégrée a été **validée par une
extraction réelle** : les volumes annoncés ci-dessous sont mesurés, pas déclarés.

## 3. Architecture de sourcing retenue (vue d'ensemble)

Trois couches complémentaires — c'est le choix structurant du projet :

| Couche | Rôle | Cadence d'ingestion |
|---|---|---|
| **Corpus annotés** (DGM4, Fakeddit, FakeNewsNet) | Charge utile d'entraînement : volumes + labels | Téléchargement unique (`@once`) |
| **Agrégateurs de fact-checking** (ClaimReview, EUvsDisinfo) | Source de vérité pour labelliser le flux | Rafraîchissement hebdomadaire |
| **Connecteurs live** (APIs presse, RSS, Bluesky) | Démonstration d'ingestion automatisée ; matière fraîche non labellisée | Quotidienne |

La complémentarité des trois corpus est voulue : **DGM4** offre des labels exacts mais
des manipulations synthétiques ; **Fakeddit** offre la diffusion réelle mais des labels
bruités ; **FakeNewsNet** offre des labels de fact-checkers humains mais des images
périssables. Chaque faiblesse est compensée par un autre corpus.

## 4. Tableau comparatif des sources retenues

| Source | Type | Appariement (champ) | Format | Langue | Labels (provenance) | Droits (base contraignante) | Extraction | Volume mesuré |
|---|---|---|---|---|---|---|---|---|
| **DGM4** | Corpus | `image` + `text` (même JSON) | JSON + zips d'images | EN | Exacts, synthétiques, 9 classes + grounding | S-Lab 1.0, recherche uniquement (le tag HF « apache-2.0 » est erroné) | Snapshot Hugging Face (10,7 Go) | **281 015** |
| **Fakeddit** | Corpus | `clean_title` + `image_url` (même ligne TSV) | TSV | EN | Supervision distante (subreddit), 2/3/6 classes | Pas de LICENSE — usage recherche par convention, non redistribuable | `gdown` (dossier Drive) | **680 798** multimodaux |
| **FakeNewsNet** | Corpus | titre CSV + image à récupérer sur la page (`og:image`) | CSV | EN | **Fact-checkers humains** (PolitiFact, GossipCop) | Repo public, contenu presse tiers — métadonnées seules redistribuables | CSV GitHub + criblage HTTP | **23 196** ; criblage : **47 %** d'images encore résolubles |
| **GDELT DOC 2.0** | API live | `socialimage` + article (même résultat JSON) | JSON | FR + 64 langues | Aucun (`unverified`) | « unlimited and unrestricted use … without fee », attribution requise — CGU lues | REST sans clé, 1 req/5 s | intégration validée |
| **The Guardian** | API live | `fields.thumbnail` (même résultat) | JSON | EN | Aucun | Open Platform, clé gratuite, usage non commercial | REST + clé | **validé en live** (7 enregistrements) |
| **NewsData.io** | API live | `image_url` (même résultat) | JSON | FR | Aucun | CGU illisibles (SPA) → posture prudente : cadre démo, attribution, pas d'assertion commerciale | REST + clé (SDK ou requests) | code prêt, clé à enregistrer |
| GNews, Currents, Mediastack, TheNewsAPI, World News API | APIs live | champ image natif (par API) | JSON | FR majoritairement | Aucun | offres gratuites, CGU par fournisseur | REST + clé, adaptateurs déclaratifs | code prêt, clés à enregistrer |
| **Flux RSS presse FR** (France Info, 20 Minutes, Le Figaro) | Flux | `media:content`/`enclosure` (même item) | XML | FR | Aucun | flux publics destinés à la syndication ; usage mesuré, pas de republication | `feedparser` | **rendement image : 94–100 %** |
| **Flux satire** (Le Gorafi, Nordpresse, The Onion) | Flux | `og:image` de la page article (repli) | XML+HTML | FR/EN | **Satire auto-déclarée** = classe à part entière | satire assumée publiquement | `feedparser` + repli `og:image` | 0 % en flux → **100 %** via repli (mesuré) |
| **Bluesky** | API sociale | `embed.images[].fullsize` + texte (même post) | JSON | EN surtout | Aucun | CGU permissives pour la recherche — **seul réseau social vérifié conforme** | REST publique sans clé | validé (auteurs pseudonymisés) |
| **Webz.io fake-news-dataset** | Corpus + flux hebdo | `thread.main_image` + `text` (même JSON) | ZIPs de JSON (GitHub) | EN 60%, RU 27%, ES/AR/ZH… | **Source-flaggé** (listes Wikipedia + filtre Webz) — faible, jamais un verdict | CGU Webz.io (licence de service) ; flag `ai_allow` par article respecté | Téléchargement incrémental + `zipfile` | **94 % d'appariement mesuré** ; ~106K articles (fév. 2025→) |
| **ClaimReview / EUvsDisinfo** | Fact-checking | revendication + verdict (pas d'image systématique) | JSON/dump | FR/EN | **Verdicts de fact-checkers** | dumps ouverts ; l'API Google FCT interdit la base permanente → usage requête ponctuelle uniquement | téléchargement de dump | à intégrer |

### Fiche détaillée — Webz.io fake-news-dataset (ajout du 2026-06-05)

**Ce que c'est.** Dépôt GitHub public de Webz.io : un drop hebdomadaire (~1 000
articles) collecté sur des sites identifiés comme éditeurs de fake news via les
listes maintenues par Wikipedia (« List of fake news websites », campagnes de
désinformation) et le filtre de confiance Webz (`trust.category:fake_news`).
106 drops de février 2025 à aujourd'hui (~106K articles), toujours actif.

**Apports.**
- **La seule source vivante avec un label « fake »** : nos connecteurs live
  produisent du contenu non vérifié, nos corpus annotés sont statiques — Webz
  fournit un flux daté du jour, côté fake. Cadence hebdomadaire = alignée sur
  notre DAG `checkit_factcheck_weekly`.
- **Appariement excellent** : 94 % des articles portent `thread.main_image`
  avec le texte intégral (médiane ~1 400 caractères) dans le même JSON — mesuré
  sur le drop du 31 mai 2026.
- **Richesse des métadonnées** : entités pré-extraites, langue, pays, rang de
  domaine, sentiment — et un **flag `ai_allow` par article** que notre
  ingestion respecte (les opt-outs ne sont jamais stockés).
- **Couverture russophone** (27 %) : fenêtre rare sur l'écosystème de
  désinformation russe.

**Limites (documentées et encodées).**
- **Label au niveau de la source, pas du contenu** : un article anodin publié
  par un site flaggé est étiqueté `fake_news` (ex. constaté : un spoiler de
  série TV). Traitement : `label_confidence = 0,5` (le plus bas de notre
  échelle), `label_source = webz-source-flagged`, et drapeau `ambiguous` sur
  les catégories divertissement/sport. À utiliser comme **signal faible**,
  jamais comme vérité terrain.
- **Pas de français** significatif (EN/RU dominants).
- **`trust.bias`** (orientation politique) présent dans les données : conservé
  brut en `extras`, **jamais utilisé comme label de véracité** (notre règle).
- **Droits** : CGU de licence de service (pas de moissonnage de PII, pas de
  démarchage commercial — sans objet pour nous), droit israélien ; contenu
  sous responsabilité des éditeurs d'origine. Posture identique au reste du
  projet : usage de recherche non commercial, jamais de redistribution.

## 5. Sources écartées — et pourquoi

L'écart est documenté sur pièces (« plus étant mieux » vaut aussi pour les refus motivés) :

| Source | Motif d'écart |
|---|---|
| **Telegram** (canaux publics) | Les conditions de licence de contenu interdisent explicitement la collecte pour l'apprentissage automatique. |
| **Mastodon** | Aucune concession de droits par les CGU + `robots.txt` interdisant les agents automatisés. |
| **Google Fact Check Tools (en masse)** | CGU interdisant la constitution d'une base permanente ; pas d'appariement image. Conservé en **requête ponctuelle** uniquement. |
| **X/Twitter** | Accès API payant à un niveau incompatible avec un projet de formation. |
| **Common Crawl / CC-NEWS** | Licence du *service*, pas du contenu ; clause d'indemnisation visant explicitement l'usage IA/ML ; appariement à reconstruire soi-même. Disproportionné ici. |
| **MMFakeBench** | Accès sous condition, redistribution interdite — réservé à l'évaluation finale, en local. |
| **Scraping de la presse française** | Opt-out TDM (art. 4 dir. UE 2019/790) répandu (AFP, Le Monde…) + exposition pénale en cas de contournement de protections (art. 323-1 s. C. pén.). **Canaux officiels d'abord** — seuls les flux RSS publics sont utilisés, sans republication. |
| GDELT **GKG brut** (vs DOC 2.0) | Volume firehose disproportionné ; DOC 2.0 suffit et porte le même appariement. |

## 6. Cas typiques de fake news multimodales couverts

Le sourcing couvre les archétypes établis (taxonomie de Wardle) :

- **Faux contexte / image détournée** : image authentique, légende mensongère — cœur de cible des détecteurs texte-image (NewsCLIPpings-like ; présent dans Fakeddit `false connection`).
- **Contenu manipulé** : visage permuté, attribut facial altéré, texte réécrit — DGM4 en fournit 152 574 cas avec localisation exacte (boîte image, positions de tokens).
- **Contenu imposteur** : faux compte/faux média — couvert par FakeNewsNet (PolitiFact).
- **Satire** : Le Gorafi, The Onion — volontairement présent comme **classe distincte**, jamais fusionnée avec la désinformation (cf. §9).
- **Désinformation politique vérifiée** : verdicts PolitiFact (FakeNewsNet) et flux de fact-checking.

## 7. Champs indispensables — l'enveloppe commune `RawRecord`

Chaque source parle son dialecte (GDELT dit `socialimage`, NewsData dit `image_url`,
Fakeddit dit `clean_title`…). Plutôt que de propager 12 schémas, **chaque extracteur
traduit vers une enveloppe unique**, validée à l'entrée (Pydantic) :

| Champ | Type | Rôle |
|---|---|---|
| `record_id` | UUID5 déterministe (url + image_url) | identité stable → déduplication et chargements **idempotents** |
| `raw_source` | str | connecteur d'origine (`gdelt-doc`, `rss:legorafi`, `fakeddit`…) — métriques par source |
| `headline` | str | titre — signal NLP principal |
| `body_text`, `caption` | str\|null | corps et légende — la légende est un signal multimodal central |
| `image_url` | str\|null | **le champ d'appariement** ; sa validation effective produit `paired_ok` |
| `url` | str\|null | provenance, audit, déduplication |
| `publish_date` | datetime UTC\|null | normalisée quel que soit le format source (ISO, epoch, RFC 822) |
| `language` | str\|null | routage FR/EN, filtres |
| `source_domain` | str\|null | indice de crédibilité + ancrage juridique |
| `raw_source_id` | str\|null | identifiant natif (re-jointures, ex. `submission_id` Fakeddit) |
| `author_pseudo_id` | hash salé\|null | **pseudonymisation RGPD** (Bluesky) — jamais de handle en clair |
| `crawl_date` | datetime UTC | date de collecte — fraîcheur et traçabilité des droits |
| `extras` | dict | tout le spécifique source, **conservé intact** (labels bruts, grounding, etc.) |

Principe : **couche brute = fidélité, couche transformée = interprétation**. Exemple
concret : les labels Fakeddit sont des entiers dont la convention doit être vérifiée
contre la publication — ils restent bruts dans `extras` et ne seront interprétés (et
testés) qu'à l'étape de transformation. Les champs calculés (hachages SHA-256 et pHash
d'image, `paired_ok`, `label` normalisé, `label_source`, `label_confidence`) sont
ajoutés par la transformation (étape 3).

## 8. Formats de sortie

**JSONL en couche brute → Parquet en couche propre → index CSV de contrôle.**

- **JSONL** (un objet JSON par ligne) pour l'acquisition : ajout en fin de fichier sans
  réécriture, robuste aux interruptions (une ligne tronquée ne corrompt pas le fichier),
  lisible en flux à mémoire constante, et schéma libre — indispensable quand 12 sources
  hétérogènes atterrissent dans la même couche.
- **Parquet** pour le jeu de données exploitable : stockage **en colonnes** (lectures
  sélectives), **types embarqués** (dates, booléens, listes survivent au cycle
  écriture/lecture), compression 5–10×, statistiques par bloc, et standard de fait de
  l'écosystème ML (pandas, Spark, Hugging Face). Un CSV unique aurait perdu les types,
  mutilé les champs listes, et souffert des virgules/guillemets des titres français.
- **Index CSV** mince (id, titre, label, source, paired_ok) pour l'inspection humaine
  sans outillage.

CSV/JSON, cités par le brief, sont traités comme la base de référence ; le passage à
JSONL/Parquet est un choix argumenté, pas un réflexe.

## 9. Opinions controversées ≠ désinformation — et la satire à part

- **Opinion controversée** : jugement subjectif, clivant, mais relevant de la liberté
  d'expression. *Ne doit jamais être labellisée « fake »*. Garde-fou : seules les
  **affirmations factuelles vérifiables** reçoivent un label de véracité ; les axes de
  *bias* politique des agrégateurs ne sont **pas** utilisés comme label (seul l'axe
  *factualité* l'est) ; les cas limites portent un drapeau `ambiguous` plutôt qu'un
  label forcé.
- **Satire** : fausse au sens littéral mais sans intention de tromper — classe
  **distincte** (`satire`) dans la taxonomie finale `{real, fake, satire, unverified}`,
  alimentée par des sources auto-déclarées (Le Gorafi, The Onion) et préservée dans les
  taxonomies fines (Fakeddit 6 classes la distingue aussi).
- La taxonomie native de chaque corpus est conservée (`fine_grained_label`) à côté du
  label agrégé : aucune information n'est détruite à l'ingestion.

## 10. Choix de conception transverses

- **Modularité** : un module par source derrière l'enveloppe commune ; fonctions pures
  (sans dépendance à l'orchestrateur) — l'étape 4 les enveloppera dans des tâches
  Airflow sans refactor. Adaptateurs d'APIs **déclaratifs** (un spec par fournisseur).
- **Robustesse mesurée en conditions réelles** : throttle GDELT (1 req/5 s constaté),
  pagination Bluesky interrompue proprement sur blocage WAF (résultats partiels
  conservés), repli `og:image` pour les flux satire (0 % d'images en flux → 100 % via
  la page), limite de champ CSV relevée (lignes virales Fakeddit > 128 Ko).
- **Skip-if-no-key** : une source sans clé est ignorée avec un log explicite, jamais une
  erreur — le pipeline multi-sources tourne avant que toutes les clés existent.
- **Secrets** : clés en variables d'environnement (`.env` non versionné), jamais en dur.
- **Droits intégrés au code** : user-agent identifiant le projet, quotas respectés,
  images conservées localement et jamais redistribuées, `license_flag` par source.
- **RGPD** : identifiants d'auteurs sociaux pseudonymisés (hash salé), handles jamais stockés.
- **Idempotence** : identifiants déterministes + (étape 4) `ON CONFLICT DO NOTHING`.
- **Qualité gouvernée par les tests** : 67 tests hermétiques (<1 s), validation live
  systématique de chaque connecteur.

## 11. Synthèse

Le dispositif retenu fournit dès aujourd'hui (volumes mesurés) :

- **985 009 enregistrements annotés** en couche brute : 281 015 (DGM4, labels exacts
  9 classes) + 680 798 (Fakeddit, multimodal, supervision distante) + 23 196
  (FakeNewsNet, fact-checkers humains, appariement image mesuré à 47 %) ;
- **132 enregistrements live appariés** validant la chaîne d'ingestion quotidienne
  (RSS FR 94–100 % d'images, Guardian validé avec clé, Bluesky conforme et
  pseudonymisé), extensible à 7 APIs presse par simple ajout de clés ;
- une couche fact-checking à venir (dumps ClaimReview/EUvsDisinfo) pour labelliser le flux ;
- un cadre de droits documenté source par source, avec les écarts motivés.

Prochaine étape (étape 2/3 du projet) : consolidation des scripts d'extraction et
pipeline de transformation vers le schéma cible, avec `paired_ok` et le taux
d'appariement comme indicateurs de référence.
