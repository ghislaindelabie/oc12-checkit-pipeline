# Schéma conceptuel des données — CheckIt.AI

**Livrable de l'étape 3** (avec le pipeline de transformation). Modèle **conceptuel** :
il décrit la signification métier des données, indépendamment de toute technologie.
Le modèle **physique** (tables SQL, types, index, clés, rôles) est volontairement
distinct et sera livré à l'étape 4 (`db/schema.sql`) — ne pas confondre les deux.

## Entités et relations

Quatre entités expriment les trois préoccupations du domaine : la **multimodalité**
(PUBLICATION↔IMAGE), la **provenance des labels** (PUBLICATION↔LABEL, 0..N car des
verdicts peuvent diverger — capturé par `ambiguous`), la **crédibilité et les droits**
(PUBLICATION↔SOURCE). IMAGE est modélisée 1..N même si la démo n'en matérialise
qu'une par publication.

```mermaid
erDiagram
    SOURCE ||--o{ PUBLICATION : "émet"
    PUBLICATION ||--|{ IMAGE : "est appariée à"
    PUBLICATION ||--o{ LABEL : "reçoit un verdict"

    PUBLICATION {
        string record_id PK "identité déterministe (idempotence)"
        string headline "titre nettoyé — signal NLP"
        string body_text "corps (souvent tronqué côté APIs)"
        string caption "légende — signal multimodal central"
        date publish_date "date de publication (UTC)"
        string url "provenance, audit"
        string language "routage FR/EN"
        string source_domain FK
        boolean paired_ok "propriété de qualité phare"
        string pairing_basis "validated | bundled | declared | none"
        string raw_source "connecteur d'origine"
        string raw_source_id "identifiant natif (re-jointures)"
        datetime crawl_date "date de collecte"
        string text_fingerprint "clé de déduplication textuelle"
        boolean is_valid "porte qualité (KPI valid_rate)"
    }
    IMAGE {
        string image_id PK
        string publication_id FK
        string image_url "pointeur source"
        string local_image_path "binaire local — jamais redistribué"
        string image_hash "SHA-256 — doublons exacts"
        string image_phash "hachage perceptuel — quasi-doublons"
        string image_source_type "news_photo | social | ai_generated…"
    }
    LABEL {
        string label_id PK
        string publication_id FK
        string label "real | fake | satire | unverified"
        string fine_grained_label "taxonomie native conservée"
        string label_source "qui a labellisé (provenance)"
        float label_confidence "1.0 synthétique > 0.9 fact-checker > 0.6 distant"
        boolean ambiguous "cas limites — jamais forcés"
        string fact_check_url "piste d'audit"
    }
    SOURCE {
        string source_domain PK
        string source_kind "api | rss | social | corpus | factcheck"
        string license_flag "valeur CONTRAIGNANTE, pas marketing"
        boolean robots_txt_allows "conformité loggée"
    }
```

## Lecture du modèle pour le cas d'usage IA

- **Classification** : `label` (cible), `label_confidence` (pondération des
  échantillons), `fine_grained_label` (tâches fines : type de manipulation DGM4,
  6 classes Fakeddit).
- **NLP** : `headline`, `body_text`, `caption` — la paire (`caption`, IMAGE) porte
  les signaux de cohérence texte-image (désinformation par fausse association).
- **Vision / multimodal** : `local_image_path` (binaire), `image_phash`
  (quasi-doublons, réutilisation hors contexte), `image_source_type` (stratification).
- **Qualité pipeline** : `paired_ok` + `pairing_basis` (KPI d'appariement strict vs
  déclaré), `is_valid` + `validation_errors` (taux de validité), `text_fingerprint`
  + `image_hash` (taux de doublons).

## Choix de modélisation justifiés

1. **LABEL séparé de PUBLICATION (0..N)** : une publication peut recevoir plusieurs
   verdicts (fact-checkers divergents) ; la provenance (`label_source`) et la
   confiance restent attachées à chaque verdict, pas à la publication.
2. **IMAGE séparée (1..N)** : exprime la multimodalité comme relation de première
   classe ; les hachages vivent avec l'image, pas avec le texte.
3. **`pairing_basis` à 4 valeurs** : distinguer une image *validée* (téléchargée,
   vérifiée Pillow), *embarquée* (corpus local), *déclarée* (URL non encore
   résolue) ou *absente* rend le KPI d'appariement honnête — un taux strict et un
   taux déclaré sont publiés séparément.
4. **Identités déterministes** : `record_id` est dérivé du contenu (URL, ou
   image+texte pour les corpus) — re-exécuter le pipeline ne crée jamais de
   doublons (chargements idempotents à l'étape 4). La justesse de cette identité a
   été validée empiriquement : la déduplication DGM4 retombe exactement sur les
   230 000 échantillons canoniques du papier (152 574 manipulés / 77 426 originaux).
