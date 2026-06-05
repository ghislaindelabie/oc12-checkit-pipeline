# OC12 — Domain, Labeling & Legal/Ethical Foundations

_Scope: domain knowledge, detection signals, labeling methodology, legal/ethical constraints, and implied data schema for a multimodal (text + image) fake-news detection pipeline built by CheckIt.AI (France-based)._

---

## 1. Multimodal Fake-News Detection — State of the Field

### What is "multimodal" fake news?

Fake news has evolved far beyond text-only articles. It now routinely exploits the combination of image and text to amplify deception: a compelling photograph lends perceived credibility to a false caption; a manipulated image reinforces a fabricated story. Modern detectors must therefore reason jointly over both modalities and their **consistency** (or lack thereof).

### Canonical signals used by multimodal detectors

Recent surveys and systems ([Springer 2025 survey](https://link.springer.com/article/10.1007/s44443-025-00317-7); [PMC MCNN paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9759663/); [Frontiers contrastive learning 2024](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2024.1473457/full)) identify the following detection signals:

| Signal category | What is measured | How it is captured |
|---|---|---|
| **Text semantics** | Topic, claim, tone, emotional polarity | BERT / RoBERTa embeddings, BiGRU sequence models |
| **Image content** | Scene, entities, emotional regions | ResNet/ViT visual encoders with attention |
| **Text–image semantic consistency** | Do the image and caption describe the same event/entity? | CLIP similarity, cosine distance in shared embedding space |
| **Named-entity match** | Are the people/places named in the caption actually visible in the image? | Face recognition, named-entity recognition (NER), cross-modal entity alignment |
| **Image physical integrity** | Signs of JPEG re-compression, splicing, GAN artefacts | Error Level Analysis (ELA), frequency-domain forensics |
| **Deepfake / AI-generation traces** | Facial manipulation (swap, attributes), GAN fingerprints | Forensic CNNs, DGM4-style grounding ([arXiv:2304.02556](https://arxiv.org/pdf/2304.02556)) |
| **Source credibility** | Known-disreputable domain, impersonating a trusted outlet | Domain allowlist/blocklist, URL pattern matching |
| **Social propagation** | Retweet velocity, engagement anomalies | Graph-based features (FakeNewsNet social context) |

The DGM4 dataset (230 k news pairs, ~77 k pristine + ~152 k manipulated) specifically benchmarks **multi-modal media manipulation**, combining face-swap, face-attribute, and text-swap manipulations — highlighting that manipulation can occur in the text, the image, or both simultaneously ([arXiv DGM4](https://arxiv.org/pdf/2304.02556)).

### What fields MUST be extracted?

Given the above signals, every record in the training pipeline **must** contain at minimum:

- The article/post **body text** (for semantic content and NER)
- The **image** (binary or URL) paired with the text
- The **caption / headline** exactly as published (separate from the body — the mismatch between headline and image is itself a signal)
- **Source domain** (for credibility features)
- **Publish date** (for temporal consistency and event-entity alignment)
- **URL** (for provenance and retrieval validation)

Omitting any of these reduces a multimodal detector to a unimodal one; several papers show that models tested without genuine multimodal inputs fall into **unimodal bias** (see §3 on VERITE).

---

## 2. Typical Multimodal Fake-News Archetypes

The canonical taxonomy comes from Claire Wardle (First Draft, 2017), arranged from least to most intentionally deceptive ([First Draft — Understanding Information Disorder](https://firstdraftnews.org/long-form-article/understanding-information-disorder/)):

| # | Archetype | Description | Multimodal signature |
|---|---|---|---|
| 1 | **Satire / Parody** | Clearly labeled humor that loses context when reshared | Image often matches the joke; text is exaggerated/absurdist |
| 2 | **False Connection** | Headline / caption does not match the image or story body | Headline–image CLIP similarity is low; body contradicts headline |
| 3 | **Misleading Content** | Genuine facts, selectively omitted or reframed | Image may be authentic; body text cherry-picks statistics |
| 4 | **False Context** | Authentic image + genuine caption, but placed in a false context | Real image + real caption from a *different* event (the OOC archetype) |
| 5 | **Imposter Content** | Genuine outlet logo/byline used to spread falsehoods | Metadata: URL resembles but doesn't match the source |
| 6 | **Manipulated Content** | Authentic media digitally altered (crop, composite, GAN face-swap) | ELA artefacts; deepfake signals; entity mismatch in image |
| 7 | **Fabricated Content** | Entirely invented text and/or synthesised image | AI-generated image fingerprints; text has no verifiable source |

**Key implication for schema:** archetypes 4 and 6 are the most frequent in benchmark datasets (NewsCLIPpings, VERITE, DGM4) and are the hardest to detect with text-only or image-only models — they require a **joint** record with both modalities stored together.

---

## 3. Labeling — How True/Fake Labels are Produced and How Reliable They Are

### 3.1 Label production methods

**Professional fact-checkers (gold standard)**

PolitiFact and GossipCop are the two dominant sources in news fake-news datasets. PolitiFact uses a 6-class scale: *True, Mostly True, Half True, Mostly False, False, Pants on Fire*. Research pipelines typically collapse this to binary: {Mostly False, False, Pants on Fire} → fake; {Mostly True, True} → real. Discarding "Half True" is common but introduces a **selection bias** toward unambiguous cases ([Guide to Misinformation Detection Datasets, arXiv 2411.05060](https://arxiv.org/html/2411.05060v1)).

GossipCop assigns a numerical score 0–10; scores < 5 are mapped to fake, news from E! Online baseline is mapped to real ([FakeNewsNet paper](https://ar5iv.labs.arxiv.org/html/1809.01286)).

Snopes and Reuters are used in VERITE ([VERITE paper](https://link.springer.com/article/10.1007/s13735-023-00312-6)) for a tighter three-class schema: *Truthful / Out-of-context / Miscaptioned*.

**Distant supervision via subreddits (Fakeddit)**

Fakeddit (Nakamura et al., 2019) labels over 1 million Reddit posts by treating certain subreddits (e.g. r/TheOnion, r/satire) as fake and others (e.g. r/worldnews, r/politics) as real. This is cheap at scale but inherits **subreddit-level noise**: a post in r/worldnews can still be misleading, and satire is not the same as disinformation. Fakeddit's 6-way scheme — *True Reporting, Satire, Misleading Content, Imposter Content, Manipulated Content, Fabricated Content* — is the most granular publicly available label set ([Fakeddit paper, arXiv:1911.03854](https://arxiv.org/abs/1911.03854)).

### 3.2 Label reliability and known failure modes

| Issue | Manifestation | Mitigation |
|---|---|---|
| **Label noise from distant supervision** | Reddit-derived labels reflect community culture, not ground truth | Restrict to subreddits with strong signal; apply label-reliability estimation ([arXiv:2206.12260](https://arxiv.org/pdf/2206.12260)) |
| **Spurious keyword correlations** | In TruthSeeker2023, "nearly all tweets mentioning politicians are labeled false" — a model learns the keyword, not the claim ([arXiv 2411.05060](https://arxiv.org/html/2411.05060v1)) | Audit label–feature correlations before training; de-bias splits |
| **Temporal correlations** | Twitter15/16 datasets: timestamp alone is predictive of veracity | Use random (not time-based) train/test splits; include publish_date as a field but not as a feature |
| **Political bias** | PolitiFact: false claims skew Republican (19.4%) vs Democratic (9.4%) | Stratify by political lean; report per-group performance metrics |
| **Class imbalance** | Real news is far more common than verified fake news | Oversample / undersample; report precision/recall/F1, not just accuracy |
| **Unimodal bias** | NewsCLIPpings and similar OOC datasets suffer from an artefact where each image appears once as "true" and once as "OOC", making image-only classifiers trivially powerful ([VERITE](https://link.springer.com/article/10.1007/s13735-023-00312-6)) | Use VERITE's **modality-balanced** splits; never reuse the same image across true/false pairs |

### 3.3 The opinion-vs-disinformation distinction — operationally

This is the most important and underserved boundary in the literature ([arXiv:2411.05060](https://arxiv.org/html/2411.05060v1); [Springer AI & Society 2025](https://link.springer.com/article/10.1007/s00146-025-02324-8)).

**Definition-level distinction** ([First Draft](https://firstdraftnews.org/long-form-article/understanding-information-disorder/)):

- **Disinformation**: objectively false claim + intentional deception. Example: "Vaccine X causes autism" accompanied by a fabricated study image.
- **Misinformation**: false but shared in good faith (e.g., outdated statistics reshared innocently).
- **Controversial opinion**: subjective judgment, values-based claim. Example: "Immigration is bad for France." Not verifiable true/false.
- **Satire**: humor with no deception intent. Becomes mis/disinfo only when reshared without context.

**Operational rules for CheckIt.AI pipeline:**

1. **Only label claims that are factually verifiable** (specific statistics, event claims, attribution quotes). Do NOT ingest pure opinion pieces or editorial columns unless a specific factual sub-claim is being checked.
2. **Use a label source field** — track whether the label comes from a professional fact-checker (PolitiFact, Snopes), a media watchdog, or distant supervision (subreddit). Treat subreddit-derived labels with lower confidence.
3. **Keep satire as a separate class** — do not collapse it into "fake." Satire label = Fakeddit category 2 or explicit `satire` metadata from the source.
4. **Preserve the 6-class or 3-class labels** in storage and only collapse to binary at training time, so future fine-grained work remains possible.
5. **Log ambiguous cases** — items where human reviewers disagree or where the claim is borderline opinion. Create a `label_confidence` field (float 0–1) or an `ambiguous` boolean.

---

## 4. Legal & Ethical Constraints for Data Acquisition (EU/France)

### 4.1 Web scraping legality in France

**CNIL position (2024 guidance)**

France's data protection authority has published explicit guidance on web scraping for AI ([CNIL focus sheet](https://www.cnil.fr/en/legal-basis-legitimate-interest-focus-sheet-measures-implement-case-data-collection-web-scraping); [BCLP analysis](https://www.bclplaw.com/en-US/events-insights-news/web-scraping-for-ai-training-in-france.html)):

- The most applicable legal basis is **legitimate interest** (GDPR Art. 6(1)(f)), not consent (impractical at scale). The scraper must still pass a three-part balancing test: purpose legitimate → necessary → interests/rights of data subjects not overridden.
- **robots.txt is legally significant**: CNIL states that ignoring a `Disallow` directive is a strong negative factor in a legitimate-interest assessment. Repeatedly bypassing technical protections (robots.txt, CAPTCHAs, rate limits) can constitute an attack on automated data processing systems (STAD) — a **criminal offence** under French law punishable by 2 years imprisonment and €60,000 fine.
- Scrapers must define collection criteria in advance, immediately delete irrelevant or sensitive data, and avoid combining data using individual identifiers.
- Even "publicly accessible" pages can contain personal data requiring GDPR protections — the **KASPR fine (€240,000)** confirmed this ([CNIL KASPR decision](https://www.cnil.fr/en/data-scraping-kaspr-fined-eu240000)).

**What CheckIt.AI must do:**

- Before scraping any site: check and store `robots.txt` state for that domain.
- Maintain a per-source `robots_txt_allows_scraping` boolean in the pipeline metadata.
- Implement exponential backoff + rate limiting; log crawl user-agent.
- Do not scrape platforms that prohibit it in ToS and also deploy robots.txt restrictions (double-layer block).

### 4.2 GDPR personal data in social content

- Social media posts, profile pictures, and user-generated images can be personal data even when public ([GDPR & web scraping, Dastra](https://www.dastra.eu/en/guide/gdpr-and-web-scraping-a-legal-practice/56357)).
- For research with genuine public-interest justification, **GDPR Art. 85** (freedom of expression / journalism) and **Art. 89** (archiving / scientific research) may provide derogations — but these are implemented differently per Member State and France's *Loi Informatique et Libertés* applies.
- Practical rule: **pseudonymise or remove author names, user IDs, and profile pictures** from training data unless strictly necessary. Store only URLs (not full scraped author profiles).

### 4.3 EU Text and Data Mining (TDM) exceptions — DSM Directive Arts. 3 & 4

([Wolters Kluwer Copyright Blog](https://legalblogs.wolterskluwer.com/copyright-blog/the-new-copyright-directive-text-and-data-mining-articles-3-and-4/); [Reed Smith](https://www.reedsmith.com/articles/entertainment-and-media-guide-to-ai/text-and-data-mining-in-eu/); [EU AI Act requirements](https://www.bclplaw.com/en-US/events-insights-news/web-scraping-for-ai-training-in-france.html))

| | **Article 3** | **Article 4** |
|---|---|---|
| **Who** | Research organisations & cultural heritage institutions | Any entity, including commercial |
| **Purpose** | Scientific research only | Any TDM purpose |
| **Opt-out by rights-holder** | **No** — unwaivable | **Yes** — rights-holder may expressly reserve rights (machine-readable means, robots.txt metadata, ToS) |
| **Lawful access required** | Yes | Yes |
| **Practical use for CheckIt.AI** | Only if CheckIt.AI has a formal research partnership with a qualifying institution | The default commercial path — but every major news publisher can and does block it |

**Critical implication**: major French and European news publishers (Le Monde, AFP, Reuters, AP) routinely add TDM opt-out declarations in their robots.txt or site ToS. Under Art. 4, CheckIt.AI **cannot train on their content** without a separate licensing agreement. The EU AI Act (in force 2025) further mandates that general-purpose AI providers document their TDM compliance.

**Practical path**: prefer **open-licensed datasets** (Creative Commons images, datasets with explicit CC0 or CC-BY research licences like those on Zenodo), or commercially licensed news APIs (Bing News, GDELT), or officially licensed academic datasets (FakeNewsNet, VERITE, NewsCLIPpings — all distributed under research-only terms).

### 4.4 Copyright on news text & images

- News article text is protected by copyright the moment it is written (no registration needed in France or EU).
- Press photographs taken by AFP/Reuters/AP photographers are fully copyrighted and covered by specific press photo licensing; redistribution requires a licence.
- **Redistribution of scraped images or full article text is high-risk** regardless of the TDM exception — the TDM exception allows *mining* (extracting features, embeddings) but not *redistribution* of the raw content ([IAPP web scraping in EU](https://iapp.org/news/a/the-state-of-web-scraping-in-the-eu)).
- This means: store **image URLs + extracted feature vectors / embeddings**, not binary image blobs, when the source is copyrighted. Or obtain images only from CC-licensed sources.

### 4.5 Practical do/don't list

| Do | Don't |
|---|---|
| Respect robots.txt and crawl-delay directives | Bypass or ignore `Disallow` directives |
| Use official APIs where available (e.g., Twitter/X Academic API, Reddit API with ToS compliance) | Scrape platforms that explicitly prohibit it in ToS |
| Prefer officially released research datasets (FakeNewsNet, Fakeddit, VERITE, NewsCLIPpings) | Redistribute full scraped article text or press photographs |
| Store image URL + hash + embedding; do not store full copyrighted image binaries | Store full JPEG/PNG of copyrighted news images without a licence |
| Pseudonymise / remove author names, profile pictures, user IDs from training data | Include identifiable personal data of private individuals in the training set |
| Document TDM compliance per source (Art. 4 opt-out check at crawl time) | Assume an absence of opt-out; affirmatively verify and log |
| Use CC0 / CC-BY licensed image sources (Wikimedia Commons, GDELT image stream) | Treat "publicly accessible" = "free to use" for training |
| Implement data minimisation: collect only what is needed for detection | Mass-collect social graph data, user profiles, or engagement metrics without a specific model justification |
| Maintain a per-record provenance field (source domain, crawl date, ToS/robots status at crawl time) | Aggregate datasets without per-record source tracking |
| When using satire or parody, label explicitly — do not conflate with disinformation | Silently drop satire examples or fold them into "fake" class |

---

## 5. Implications for the Data Schema — Required Fields

Synthesising the multimodal signal requirements (§1), the labeling methodology (§3), and the legal provenance obligations (§4), every record in the CheckIt.AI training corpus **must** carry the following fields:

### Mandatory fields

| Field | Type | Why required |
|---|---|---|
| `record_id` | string (UUID) | Deduplication and provenance tracing |
| `headline` | string | False-connection signal: headline vs image vs body mismatch |
| `body_text` | string or null | Semantic content for NLP models; null if image-only post |
| `image_url` | string (URL) | Pointer to image; mandatory for multimodal pair |
| `image_hash` | string (SHA-256) | Deduplication; detect recycled/reused images |
| `caption` | string or null | The literal caption as published (may differ from headline) |
| `label` | enum {real, fake, satire, unverified} | Target variable |
| `label_source` | string | e.g. "PolitiFact", "Snopes", "Fakeddit-subreddit", "GossipCop" |
| `label_confidence` | float [0,1] or null | Reliability weight; lower for distant-supervision labels |
| `fine_grained_label` | string or null | Wardle archetype or Fakeddit 6-class; preserved before any binary collapse |
| `publish_date` | ISO-8601 date | Event–entity temporal alignment; temporal-bias auditing |
| `source_domain` | string (e.g. "lemonde.fr") | Source credibility feature; legal provenance |
| `url` | string | Original article URL; required for GDPR provenance and audit |
| `language` | BCP-47 code (e.g. "fr", "en") | Multilingual pipeline routing |
| `license_flag` | enum {cc0, cc_by, research_only, restricted, unknown} | Legal usage classification |
| `tdm_opt_out_checked` | boolean | Was Art. 4 TDM opt-out status verified at crawl time? |
| `robots_txt_allows` | boolean or null | robots.txt compliance log at crawl time |
| `crawl_date` | ISO-8601 datetime | Provenance; required for temporal validity checks |

### Recommended additional fields

| Field | Type | Why useful |
|---|---|---|
| `image_embedding` | float array (e.g. 512-d CLIP) | Pre-computed for fast similarity search; avoid storing copyrighted raw image |
| `text_embedding` | float array | Pre-computed for text-side similarity search |
| `image_source_type` | enum {news_photo, social_media, ai_generated, stock, unknown} | Stratify training; flag AI-generated images |
| `entity_persons` | string array | NER output: persons mentioned in text |
| `entity_locations` | string array | NER output: locations |
| `subreddit` | string or null | For Fakeddit-derived records |
| `fact_check_url` | string or null | URL of the fact-checking article that produced the label |
| `ambiguous` | boolean | Flag for human-review borderline cases (opinion-adjacent) |

---

## Required Fields Implied by the Domain — Summary Bullet List

- **`headline`** — false-connection detection (headline vs image)
- **`body_text`** — NLP semantics, entity extraction
- **`image_url` + `image_hash`** — multimodal pair, deduplication
- **`caption`** — separate from headline; the literal text paired with the image
- **`label`** + **`label_source`** + **`fine_grained_label`** — target, provenance, Wardle archetype
- **`label_confidence`** — reliability weight for noisy distant-supervision labels
- **`publish_date`** — temporal consistency; bias auditing
- **`source_domain`** — credibility feature; legal provenance
- **`url`** — GDPR provenance, audit, deduplication
- **`language`** — multilingual routing
- **`license_flag`** — legal usage classification (cc0 / research_only / restricted)
- **`tdm_opt_out_checked`** + **`robots_txt_allows`** — legal compliance log
- **`crawl_date`** — provenance and freshness tracking

---

## Sources

1. [Springer 2025 — Multi-modal fake news detection: A comprehensive survey](https://link.springer.com/article/10.1007/s44443-025-00317-7)
2. [Frontiers 2024 — Multimodal Fake News Detection with Contrastive Learning and Optimal Transport](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2024.1473457/full)
3. [PMC — Detecting fake news by exploring the consistency of multimodal data (MCNN)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9759663/)
4. [arXiv:2304.02556 — Detecting and Grounding Multi-Modal Media Manipulation (DGM4)](https://arxiv.org/pdf/2304.02556)
5. [arXiv:2104.05893 — NewsCLIPpings: Automatic Generation of Out-of-Context Multimodal Media](https://arxiv.org/abs/2104.05893)
6. [VERITE: A Robust Benchmark for Multimodal Misinformation Detection (Springer)](https://link.springer.com/article/10.1007/s13735-023-00312-6)
7. [arXiv:1911.03854 — r/Fakeddit: A New Multimodal Benchmark Dataset](https://arxiv.org/abs/1911.03854)
8. [ar5iv — FakeNewsNet: News Content, Social Context, Spatiotemporal Information](https://ar5iv.labs.arxiv.org/html/1809.01286)
9. [arXiv:2411.05060 — A Guide to Misinformation Detection Datasets](https://arxiv.org/html/2411.05060v1)
10. [First Draft — Understanding Information Disorder (Wardle taxonomy)](https://firstdraftnews.org/long-form-article/understanding-information-disorder/)
11. [arXiv:2206.12260 — Label Noise-Resistant Mean Teaching for Weakly Supervised Fake News Detection](https://arxiv.org/pdf/2206.12260)
12. [Springer AI & Society — The Limits of Machine Learning Models of Misinformation](https://link.springer.com/article/10.1007/s00146-025-02324-8)
13. [CNIL — Legal basis of legitimate interest: focus sheet on web scraping](https://www.cnil.fr/en/legal-basis-legitimate-interest-focus-sheet-measures-implement-case-data-collection-web-scraping)
14. [CNIL — Data scraping: KASPR fined €240,000](https://www.cnil.fr/en/data-scraping-kaspr-fined-eu240000)
15. [BCLP — Web Scraping for AI Training in France](https://www.bclplaw.com/en-US/events-insights-news/web-scraping-for-ai-training-in-france.html)
16. [IAPP — The state of web scraping in the EU](https://iapp.org/news/a/the-state-of-web-scraping-in-the-eu)
17. [Dastra — GDPR and web scraping: a legal practice?](https://www.dastra.eu/en/guide/gdpr-and-web-scraping-a-legal-practice/56357)
18. [Wolters Kluwer Copyright Blog — TDM exceptions Articles 3 and 4 (DSM Directive)](https://legalblogs.wolterskluwer.com/copyright-blog/the-new-copyright-directive-text-and-data-mining-articles-3-and-4/)
19. [Reed Smith — Text and data mining in EU](https://www.reedsmith.com/articles/entertainment-and-media-guide-to-ai/text-and-data-mining-in-eu/)
20. [GDPR-info — Article 85: Processing and freedom of expression](https://gdpr-info.eu/art-85-gdpr/)
21. [ResearchGate — A comprehensive survey of multimodal fake news detection techniques](https://www.researchgate.net/publication/373350532_A_comprehensive_survey_of_multimodal_fake_news_detection_techniques_advances_challenges_and_opportunities)
22. [MDPI — Fake News Detection Revisited: Theoretical Frameworks, Dataset Assessments](https://www.mdpi.com/2227-7090/12/11/222)
